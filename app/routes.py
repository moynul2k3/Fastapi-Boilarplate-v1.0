import importlib
from pathlib import Path
from fastapi import FastAPI, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html

ROUTES_DIR = Path(__file__).parent.parent / "routes"

AUTO_AUTH_SWAGGER_SCRIPT = """
<script>
(() => {
  const tryAuthorize = (token) => {
    if (!window.ui || !token) return false;
    const bearerToken = `Bearer ${token}`;
    let applied = false;

    try {
      const system = window.ui.getSystem ? window.ui.getSystem() : null;
      const defsRaw = system?.specSelectors?.securityDefinitions?.();
      const defs = defsRaw?.toJS ? defsRaw.toJS() : (defsRaw || {});
      const names = Object.keys(defs || {});

      for (const name of names) {
        const def = defs[name] || {};

        if (window.ui.preauthorizeApiKey) {
          window.ui.preauthorizeApiKey(name, token);
          window.ui.preauthorizeApiKey(name, bearerToken);
        }

        if (system?.authActions?.authorize) {
          system.authActions.authorize({ [name]: { value: bearerToken } });
          system.authActions.authorize({ [name]: { value: token } });
          system.authActions.authorize({
            [name]: {
              token: { access_token: token, token_type: 'bearer' },
            }
          });
        }

        if (def.type === 'oauth2' && system?.authActions?.authorizeOauth2) {
          system.authActions.authorizeOauth2({
            auth: {
              name,
              schema: def,
              token: { access_token: token, token_type: 'bearer' },
            }
          });
        }

        applied = true;
      }
    } catch (_) {
      // Keep silent; final fallback below.
    }

    // Best-effort persistence fallback for Swagger versions that read localStorage.
    try {
      localStorage.setItem('swagger_cookie_token', token);
    } catch (_) {
      // Ignore storage failures.
    }

    return applied;
  };

  const applyAuth = async () => {
    if (!window.ui) return;
    try {
      const res = await fetch('/auth/swagger-auth-token/', { credentials: 'include' });
      if (!res.ok) return;
      const data = await res.json();
      if (!data || !data.access_token) return;
      tryAuthorize(data.access_token);
    } catch (_) {
      // Ignore silent auth sync failures.
    }
  };

  const backendLogout = async () => {
    try {
      await fetch('/auth/logout/', { method: 'POST', credentials: 'include' });
    } catch (_) {
      // Ignore logout sync failures from docs UI.
    }
  };

  const forceLogoutSync = async () => {
    await backendLogout();
    try {
      localStorage.removeItem('swagger_cookie_token');
      localStorage.removeItem('authorized');
    } catch (_) {
      // Ignore storage cleanup failures.
    }
    setTimeout(() => window.location.reload(), 120);
  };

  const attachLogoutHooks = () => {
    if (!window.ui || !window.ui.getSystem) return false;
    const system = window.ui.getSystem();
    if (!system || !system.authActions) return false;
    if (window.__swaggerLogoutHookAttached) return true;

    const authActions = system.authActions;
    const logoutActionNames = Object.keys(authActions).filter((name) =>
      name.toLowerCase().includes('logout')
    );

    for (const actionName of logoutActionNames) {
      const original = authActions[actionName];
      if (typeof original !== 'function') continue;
      authActions[actionName] = (...args) => {
        const result = original(...args);
        forceLogoutSync();
        return result;
      };
    }

    window.__swaggerLogoutHookAttached = true;
    return true;
  };

  document.addEventListener('click', async (event) => {
    const target = event.target;
    if (!target || !target.closest) return;
    const button = target.closest('button');
    if (!button) return;
    const text = (button.textContent || '').trim().toLowerCase();
    if (text !== 'logout') return;
    forceLogoutSync();
  });

  let attempts = 0;
  const timer = setInterval(() => {
    attempts += 1;
    if (window.ui) {
      attachLogoutHooks();
      clearInterval(timer);
      applyAuth();
      return;
    }
    if (attempts >= 40) {
      clearInterval(timer);
    }
  }, 150);

  // Re-apply after full UI render and route transitions.
  window.addEventListener('load', () => {
    attachLogoutHooks();
    setTimeout(applyAuth, 300);
    setTimeout(attachLogoutHooks, 500);
    setTimeout(applyAuth, 1200);
    setTimeout(attachLogoutHooks, 1400);
  });
})();
</script>
"""

def register_routes(app: FastAPI):
    def build_docs_handler(current_sub_app: FastAPI):
        async def custom_docs() -> HTMLResponse:
            response = get_swagger_ui_html(
                # Mounted apps need a relative path so docs loads that sub-app schema.
                openapi_url="./openapi.json",
                title=f"{current_sub_app.title} - Swagger UI",
                swagger_ui_parameters={
                    "persistAuthorization": True,
                    "withCredentials": True,
                },
            )
            html = response.body.decode("utf-8")
            # Expose Swagger instance globally for auth sync script.
            html = html.replace("const ui = SwaggerUIBundle(", "window.ui = SwaggerUIBundle(")
            html = html.replace("</body>", f"{AUTO_AUTH_SWAGGER_SCRIPT}</body>")
            return HTMLResponse(content=html, status_code=response.status_code)

        return custom_docs

    for sub_dir in ROUTES_DIR.iterdir():
        if not sub_dir.is_dir():
            continue

        sub_app = FastAPI(
            title=f"SubApp-{sub_dir.name}",
            docs_url=None,
            redoc_url=None,
            swagger_ui_parameters={
                "persistAuthorization": True,
                "withCredentials": True,
            },
        )
        sub_app.add_api_route("/docs", build_docs_handler(sub_app), include_in_schema=False)

        mounted = False

        for py_file in sub_dir.glob("*.py"):
            if py_file.stem.startswith("__"):
                continue

            module_path = f"routes.{sub_dir.name}.{py_file.stem}"
            try:
                module = importlib.import_module(module_path)
                if hasattr(module, "router") and isinstance(module.router, APIRouter):
                    sub_app.include_router(module.router)
                    mounted = True
                else:
                    print(f"⚠️ No 'router' in {module_path}. Skipping.")
            except Exception as e:
                print(f"⚠️ Error loading {module_path}: {e}")

        if mounted:
            app.mount(f"/{sub_dir.name}", sub_app)
