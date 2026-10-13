const pageNames = new Map([
  ['dashboard', 'Dashboard'],
  ['workspace', 'Workspace'],
  ['chat', 'AI Chat'],
  ['sandbox', 'Sandbox'],
  ['terminal', 'Terminal / Logs'],
  ['memory', 'Memory'],
  ['tasks', 'Tasks'],
  ['settings', 'Settings']
]);

const state = {
  token: null,
  user: null,
  projects: [],
  selectedProject: null,
  capabilities: null
};

const elements = {
  sidebar: document.getElementById('sidebar'),
  pageTitle: document.getElementById('pageTitle'),
  loginForm: document.getElementById('loginForm'),
  loginError: document.getElementById('loginError'),
  loginButton: document.getElementById('loginButton'),
  projectWorkspace: document.getElementById('projectWorkspace'),
  projectList: document.getElementById('projectList'),
  projectError: document.getElementById('projectError'),
  workspaceDetail: document.getElementById('workspaceDetail')
};

function setPage(page, updateHash = true) {
  if (!pageNames.has(page)) return;

  document.querySelectorAll('.nav-item[data-page]').forEach((item) => {
    const active = item.dataset.page === page;
    item.classList.toggle('active', active);
    if (active) item.setAttribute('aria-current', 'page');
    else item.removeAttribute('aria-current');
  });
  document.querySelectorAll('.page[data-page]').forEach((section) => {
    const active = section.dataset.page === page;
    section.hidden = !active;
    section.classList.toggle('active', active);
  });

  elements.pageTitle.textContent = pageNames.get(page);
  elements.sidebar.classList.remove('open');
  document.getElementById('menuToggle').setAttribute('aria-expanded', 'false');
  if (updateHash && window.location.hash !== `#${page}`) {
    window.history.replaceState(null, '', `#${page}`);
  }
  if (page === 'workspace' && state.token && !state.projects.length) {
    void loadProjects();
  }
}

async function apiRequest(path, { method = 'GET', body, authenticated = true } = {}) {
  const headers = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (authenticated && state.token) headers.Authorization = `Bearer ${state.token}`;

  const response = await fetch(path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: 'no-store'
  });
  const contentType = response.headers.get('content-type') || '';
  const data = contentType.includes('application/json')
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    if (response.status === 401 && authenticated) clearSession();
    const detail = data && typeof data === 'object' ? data.detail : null;
    throw new Error(typeof detail === 'string' ? detail : `API request failed (${response.status})`);
  }
  return data;
}

function showError(element, message) {
  element.textContent = message;
  element.hidden = false;
}

function clearError(element) {
  element.textContent = '';
  element.hidden = true;
}

function setServiceIndicator(ids, { state: status, label, detail }) {
  ids.forEach((id) => {
    const element = document.getElementById(id);
    if (!element) return;
    const dot = element.firstElementChild?.tagName === 'I'
      ? element.firstElementChild
      : null;
    if (dot) {
      dot.className = status === 'live'
        ? 'indicator-live'
        : status === 'warning'
          ? 'indicator-warning'
          : status === 'error'
            ? 'indicator-error'
            : 'indicator-muted';
      element.lastChild.textContent = label;
    } else {
      element.textContent = label;
    }
    element.classList.remove('is-live', 'is-warning', 'is-error');
    if (status === 'live') element.classList.add('is-live');
    else if (status === 'warning') element.classList.add('is-warning');
    else if (status === 'error') element.classList.add('is-error');
    if (detail) element.title = detail;
  });
}

function setIndicatorDot(id, status) {
  const element = document.getElementById(id);
  if (!element) return;
  element.className = '';
  if (status === 'live') element.classList.add('indicator-live');
  else if (status === 'warning') element.classList.add('indicator-warning');
  else if (status === 'error') element.classList.add('indicator-error');
  else element.classList.add('indicator-muted');
}

async function refreshServiceStatus() {
  const healthRequest = apiRequest('/api/v1/health', { authenticated: false });
  const capabilityRequest = apiRequest('/api/v1/sandboxes/capabilities', { authenticated: false });
  const [healthResult, capabilityResult] = await Promise.allSettled([
    healthRequest,
    capabilityRequest
  ]);

  if (healthResult.status === 'fulfilled' && healthResult.value.status === 'ok') {
    const health = healthResult.value;
    setIndicatorDot('apiIndicator', 'live');
    setServiceIndicator(['apiState', 'tableApiStatus', 'settingsApiState'], {
      state: 'live',
      label: 'Online'
    });
    document.getElementById('apiValue').textContent = 'Online';
    document.getElementById('apiCaption').textContent = `${health.service} · process health`;
    document.getElementById('tableApiDetail').textContent = 'Responding';
    document.getElementById('sidebarHealthLight').className = 'runtime-light is-live';
    document.getElementById('sidebarHealthText').textContent = 'API responding';
    document.getElementById('topbarHealthLight').className = 'runtime-light is-live';
    document.getElementById('topbarHealthText').textContent = 'Backend online';
  } else {
    const error = healthResult.status === 'rejected'
      ? healthResult.reason.message
      : 'Unexpected health response';
    setIndicatorDot('apiIndicator', 'error');
    setServiceIndicator(['apiState', 'tableApiStatus', 'settingsApiState'], {
      state: 'error',
      label: 'Unavailable',
      detail: error
    });
    document.getElementById('apiValue').textContent = 'Unavailable';
    document.getElementById('apiCaption').textContent = error;
    document.getElementById('tableApiDetail').textContent = 'Health request failed';
    document.getElementById('sidebarHealthLight').className = 'runtime-light is-error';
    document.getElementById('sidebarHealthText').textContent = 'API unavailable';
    document.getElementById('topbarHealthLight').className = 'runtime-light is-error';
    document.getElementById('topbarHealthText').textContent = 'Backend unavailable';
  }

  if (capabilityResult.status === 'fulfilled') {
    const capabilities = capabilityResult.value;
    state.capabilities = capabilities;
    const isConfigured = capabilities.state !== 'NEEDS_SETUP';
    const status = isConfigured ? 'live' : 'warning';
    const stateLabel = capabilities.state || 'Unknown';
    const capabilityDetail = capabilities.reason || 'Capability endpoint responded';
    setIndicatorDot('sandboxIndicator', status);
    setServiceIndicator(['sandboxState', 'tableSandboxStatus', 'settingsSandboxState'], {
      state: status,
      label: stateLabel,
      detail: capabilityDetail
    });
    document.getElementById('sandboxValue').textContent = stateLabel;
    document.getElementById('sandboxCaption').textContent = capabilities.provider || 'Provider not reported';
    document.getElementById('tableSandboxDetail').textContent =
      capabilities.execution_enabled ? 'Execution reported enabled' : 'Execution disabled';
    document.getElementById('sandboxBadge').textContent = stateLabel;
    document.getElementById('sandboxBadge').className =
      `badge ${isConfigured ? 'badge-live' : 'badge-warning'}`;
    document.getElementById('sandboxHeading').textContent = isConfigured
      ? 'Runtime capability reported by backend'
      : 'Runtime is not configured';
    document.getElementById('sandboxReason').textContent = capabilityDetail;
    document.getElementById('sandboxProvider').textContent = capabilities.provider || 'Not reported';
    document.getElementById('sandboxExecution').textContent =
      capabilities.execution_enabled ? 'Reported enabled' : 'Disabled';
    document.getElementById('sandboxNetwork').textContent = capabilities.network_default || 'Not reported';
  } else {
    const error = capabilityResult.reason.message;
    setIndicatorDot('sandboxIndicator', 'error');
    setServiceIndicator(['sandboxState', 'tableSandboxStatus', 'settingsSandboxState'], {
      state: 'error',
      label: 'Unavailable',
      detail: error
    });
    document.getElementById('sandboxValue').textContent = 'Unavailable';
    document.getElementById('sandboxCaption').textContent = error;
    document.getElementById('tableSandboxDetail').textContent = 'Capability request failed';
    document.getElementById('sandboxBadge').textContent = 'Status unavailable';
    document.getElementById('sandboxBadge').className = 'badge badge-muted';
    document.getElementById('sandboxHeading').textContent = 'Could not read runtime capability';
    document.getElementById('sandboxReason').textContent = error;
    document.getElementById('sandboxProvider').textContent = 'Unknown';
    document.getElementById('sandboxExecution').textContent = 'Unknown';
    document.getElementById('sandboxNetwork').textContent = 'Unknown';
  }
}

function clearSession() {
  state.token = null;
  state.user = null;
  state.projects = [];
  state.selectedProject = null;
  elements.loginForm.hidden = false;
  elements.projectWorkspace.hidden = true;
  document.getElementById('workspaceAuthBadge').textContent = 'Authentication required';
  document.getElementById('sidebarUserName').textContent = 'Guest session';
  document.getElementById('sidebarUserCaption').textContent = 'Not signed in';
  document.getElementById('sidebarSignOut').hidden = true;
}

async function handleLogin(event) {
  event.preventDefault();
  clearError(elements.loginError);
  elements.loginButton.disabled = true;
  elements.loginButton.textContent = 'Signing in…';

  try {
    const form = new FormData(elements.loginForm);
    const result = await apiRequest('/api/v1/auth/login', {
      method: 'POST',
      authenticated: false,
      body: {
        username: String(form.get('username')).trim(),
        password: String(form.get('password'))
      }
    });
    elements.loginForm.reset();
    state.token = result.access_token;
    state.user = {
      username: result.username,
      displayName: result.display_name || result.username
    };
    elements.loginForm.hidden = true;
    elements.projectWorkspace.hidden = false;
    document.getElementById('workspaceAuthBadge').textContent = `Signed in · ${state.user.username}`;
    document.getElementById('sidebarUserName').textContent = state.user.displayName;
    document.getElementById('sidebarUserCaption').textContent = 'Authenticated session';
    document.getElementById('sidebarSignOut').hidden = false;
    await loadProjects();
  } catch (error) {
    showError(elements.loginError, error.message);
  } finally {
    elements.loginButton.disabled = false;
    elements.loginButton.innerHTML = 'Sign in <span>→</span>';
  }
}

function renderProjectList() {
  elements.projectList.replaceChildren();
  if (!state.projects.length) {
    const empty = document.createElement('p');
    empty.className = 'list-empty';
    empty.textContent = 'No projects returned for this account.';
    elements.projectList.append(empty);
    return;
  }

  state.projects.forEach((project) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'project-entry';
    button.classList.toggle(
      'selected',
      state.selectedProject?.project_id === project.project_id
    );
    button.dataset.projectId = String(project.project_id);

    const mark = document.createElement('span');
    mark.className = 'project-mark';
    mark.textContent = project.project_name?.slice(0, 1).toUpperCase() || 'P';
    const detail = document.createElement('span');
    detail.className = 'project-entry-copy';
    const name = document.createElement('strong');
    name.textContent = project.project_name;
    const status = document.createElement('small');
    status.textContent = project.project_status || 'Project';
    detail.append(name, status);
    button.append(mark, detail);
    button.addEventListener('click', () => selectProject(project));
    elements.projectList.append(button);
  });
}

async function loadProjects() {
  if (!state.token) return;
  clearError(elements.projectError);
  elements.projectList.innerHTML = '<p class="list-empty">Loading projects…</p>';
  try {
    const result = await apiRequest('/api/v1/projects');
    state.projects = Array.isArray(result.items) ? result.items : [];
    if (
      state.selectedProject &&
      !state.projects.some((project) => project.project_id === state.selectedProject.project_id)
    ) {
      state.selectedProject = null;
    }
    renderProjectList();
    if (state.selectedProject) await selectProject(state.selectedProject);
  } catch (error) {
    elements.projectList.replaceChildren();
    showError(elements.projectError, error.message);
  }
}

async function selectProject(project) {
  state.selectedProject = project;
  renderProjectList();
  elements.workspaceDetail.innerHTML =
    '<div class="workspace-empty"><span class="loading-mark">↻</span><h2>Loading workspace</h2><p>Fetching project metadata from the API…</p></div>';

  try {
    const result = await apiRequest(`/api/v1/projects/${encodeURIComponent(project.project_id)}/workspaces`);
    renderWorkspaceDetail(project, Array.isArray(result.items) ? result.items : []);
  } catch (error) {
    renderWorkspaceError(project, error.message);
  }
}

function renderWorkspaceDetail(project, workspaces) {
  const wrapper = document.createElement('div');
  wrapper.className = 'workspace-detail-inner';
  const header = document.createElement('div');
  header.className = 'panel-heading';
  const identity = document.createElement('div');
  identity.innerHTML = '<span class="eyebrow">SELECTED PROJECT</span>';
  const title = document.createElement('h2');
  title.textContent = project.project_name;
  identity.append(title);
  const badge = document.createElement('span');
  badge.className = 'badge badge-live';
  badge.textContent = project.project_status || 'Project';
  header.append(identity, badge);
  wrapper.append(header);

  const description = document.createElement('p');
  description.className = 'project-description';
  description.textContent = project.description || 'No project description.';
  wrapper.append(description);

  const workspacesHeader = document.createElement('div');
  workspacesHeader.className = 'workspace-list-heading';
  const workspacesTitle = document.createElement('h3');
  workspacesTitle.textContent = 'Workspace metadata';
  const count = document.createElement('span');
  count.className = 'count-chip';
  count.textContent = String(workspaces.length);
  workspacesHeader.append(workspacesTitle, count);
  wrapper.append(workspacesHeader);

  if (!workspaces.length) {
    const empty = document.createElement('p');
    empty.className = 'list-empty workspace-list-empty';
    empty.textContent = 'No workspace metadata exists for this project.';
    wrapper.append(empty);
  } else {
    const list = document.createElement('div');
    list.className = 'workspace-list';
    workspaces.forEach((workspace) => {
      const row = document.createElement('div');
      row.className = 'workspace-entry';
      const name = document.createElement('strong');
      name.textContent = workspace.workspace_name;
      const path = document.createElement('code');
      path.textContent = workspace.storage_path;
      const status = document.createElement('span');
      status.className = 'badge badge-muted';
      status.textContent = workspace.workspace_status || 'Workspace';
      row.append(name, path, status);
      list.append(row);
    });
    wrapper.append(list);
  }

  const form = document.createElement('form');
  form.className = 'create-workspace-form';
  form.innerHTML = '<label for="workspaceName">Create workspace metadata</label><div class="inline-form"><input id="workspaceName" name="workspace_name" required minlength="1" maxlength="150" placeholder="Workspace name" /><button class="button button-primary" type="submit">Create <span>＋</span></button></div><p class="form-error" role="alert" hidden></p>';
  form.addEventListener('submit', (event) => handleWorkspaceCreate(event, project, form));
  wrapper.append(form);
  elements.workspaceDetail.replaceChildren(wrapper);
}

function renderWorkspaceError(project, message) {
  const wrapper = document.createElement('div');
  wrapper.className = 'workspace-empty';
  const title = document.createElement('h2');
  title.textContent = project.project_name;
  const error = document.createElement('p');
  error.className = 'form-error';
  error.textContent = `Could not load workspace metadata: ${message}`;
  wrapper.append(title, error);
  elements.workspaceDetail.replaceChildren(wrapper);
}

async function handleWorkspaceCreate(event, project, form) {
  event.preventDefault();
  const errorElement = form.querySelector('[role="alert"]');
  clearError(errorElement);
  const submit = form.querySelector('button[type="submit"]');
  submit.disabled = true;
  try {
    const formData = new FormData(form);
    await apiRequest(
      `/api/v1/projects/${encodeURIComponent(project.project_id)}/workspaces`,
      {
        method: 'POST',
        body: { workspace_name: String(formData.get('workspace_name')).trim() }
      }
    );
    await selectProject(project);
  } catch (error) {
    showError(errorElement, error.message);
  } finally {
    submit.disabled = false;
  }
}

async function handleProjectCreate(event) {
  event.preventDefault();
  clearError(elements.projectError);
  const button = event.currentTarget.querySelector('button[type="submit"]');
  button.disabled = true;
  try {
    const formData = new FormData(event.currentTarget);
    const project = await apiRequest('/api/v1/projects', {
      method: 'POST',
      body: {
        project_name: String(formData.get('project_name')).trim(),
        description: String(formData.get('description')).trim() || null
      }
    });
    event.currentTarget.reset();
    await loadProjects();
    await selectProject(project);
  } catch (error) {
    showError(elements.projectError, error.message);
  } finally {
    button.disabled = false;
  }
}

function bindEvents() {
  document.querySelectorAll('.nav-item[data-page]').forEach((item) => {
    item.addEventListener('click', () => setPage(item.dataset.page));
  });
  document.querySelectorAll('[data-go]').forEach((button) => {
    button.addEventListener('click', () => setPage(button.dataset.go));
  });
  document.getElementById('menuToggle').addEventListener('click', (event) => {
    const open = elements.sidebar.classList.toggle('open');
    event.currentTarget.setAttribute('aria-expanded', String(open));
  });
  document.getElementById('refreshServices').addEventListener('click', refreshServiceStatus);
  document.getElementById('refreshServicesLink').addEventListener('click', refreshServiceStatus);
  document.getElementById('settingsRefresh').addEventListener('click', refreshServiceStatus);
  document.getElementById('reloadProjects').addEventListener('click', loadProjects);
  document.getElementById('loginForm').addEventListener('submit', handleLogin);
  document.getElementById('createProjectForm').addEventListener('submit', handleProjectCreate);
  document.getElementById('sidebarSignOut').addEventListener('click', clearSession);
  window.addEventListener('hashchange', () => setPage(window.location.hash.slice(1), false));
}

function init() {
  document.getElementById('apiOrigin').textContent = window.location.origin;
  bindEvents();
  setPage(window.location.hash.slice(1) || 'dashboard', false);
  void refreshServiceStatus();
  window.setInterval(refreshServiceStatus, 30000);
}

init();
