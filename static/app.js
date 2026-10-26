const $ = (selector) => document.querySelector(selector);
const state = { displays: [], media: [], playlist: [], selectedDisplay: "main" };
let toastTimer;
async function api(url, options = {}) {
  const response = await fetch(url, options);
  if (response.status === 401) throw new Error("Admin authentication failed. Reload and sign in again.");
  if (!response.ok) {
    let detail = "Request failed (" + response.status + ")";
    try { const body = await response.json(); detail = body.detail || detail; } catch {}
    throw new Error(detail);
  }
  if (response.status === 204) return null;
  return response.json();
}
function notify(message, isError = false) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.toggle("toast-error", isError);
  toast.classList.add("toast-visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("toast-visible"), 3500);
}
function esc(value) {
  return String(value).replace(/[&<>"']/g, c => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c]));
}
function mediaIcon(item) { return item.media_type === "video" ? "▶" : "▧"; }
function currentDisplay() { return state.displays.find(d => d.id === state.selectedDisplay); }
function renderDisplays() {
  $("#display-select").innerHTML = state.displays.map(d => '<option value="' + esc(d.id) + '">' + esc(d.name) + ' · ' + esc(d.id) + '</option>').join("");
  $("#display-select").value = state.selectedDisplay;
  $("#open-player").href = "/display/" + encodeURIComponent(state.selectedDisplay);
  if ($("#control-status")) api("/api/admin/displays/" + encodeURIComponent(state.selectedDisplay) + "/control")
    .then(data => { $("#control-status").textContent = ({ play: "Playing", freeze: "Frozen", break: "Break screen" })[data.mode] || "Playing"; })
    .catch(() => {});
  $("#display-count").textContent = state.displays.length;
  $("#selected-display-label").textContent = (currentDisplay()?.name || "Selected display") + " items";
}
function renderPlaylist() {
  $("#playlist-count").textContent = state.playlist.length;
  $("#playlist-badge").textContent = state.playlist.length + " ITEMS";
  $("#playlist-help").textContent = state.playlist.length ? "Drag the list order in the next release; save to apply this sequence." : "Select assets below to add them.";
  if (!state.playlist.length) {
    $("#playlist").innerHTML = '<div class="empty-state"><span>↳</span><strong>This screen is a blank canvas.</strong><small>Add assets from the media library below.</small></div>';
    return;
  }
  $("#playlist").innerHTML = state.playlist.map((item, index) => '<div class="playlist-row" data-id="' + esc(item.id) + '"><span class="playlist-index">' + String(index + 1).padStart(2,"0") + '</span><span class="asset-icon">' + mediaIcon(item) + '</span><span class="asset-details"><strong>' + esc(item.title) + '</strong><small>' + esc(item.media_type) + ' · ' + Number(item.duration) + ' sec</small></span><div class="row-actions"><button class="icon-button move-up" aria-label="Move up" title="Move up" ' + (index === 0 ? "disabled" : "") + '>↑</button><button class="icon-button move-down" aria-label="Move down" title="Move down" ' + (index === state.playlist.length - 1 ? "disabled" : "") + '>↓</button><button class="icon-button remove-item" aria-label="Remove from playlist" title="Remove">×</button></div></div>').join("");
}
function renderLibrary() {
  $("#media-count").textContent = state.media.length;
  const playlistIds = new Set(state.playlist.map(item => item.id));
  if (!state.media.length) {
    $("#library").innerHTML = '<div class="empty-state"><strong>No media yet.</strong><small>Upload a poster, video, or PowerPoint presentation to get started.</small></div>';
    return;
  }
  $("#library").innerHTML = state.media.map(item => '<article class="library-card"><div class="library-thumb">' + (item.media_type === "image" ? '<img src="' + esc(item.url) + '" alt="" loading="lazy">' : '<span>▶</span>') + '<span class="type-pill">' + esc(item.media_type) + '</span></div><div class="library-card-body"><strong title="' + esc(item.title) + '">' + esc(item.title) + '</strong><small>' + esc(item.filename) + '</small><div class="library-actions"><button class="button button-small add-media" data-id="' + esc(item.id) + '" ' + (playlistIds.has(item.id) ? "disabled" : "") + '>' + (playlistIds.has(item.id) ? "In playlist" : "+ Add") + '</button><button class="button button-small button-danger delete-media" data-id="' + esc(item.id) + '">Delete</button></div></div></article>').join("");
}
async function loadAll() {
  try {
    const [displays, media] = await Promise.all([api("/api/admin/displays"), api("/api/admin/media")]);
    state.displays = displays;
    state.media = media;
    if (!state.displays.some(d => d.id === state.selectedDisplay)) state.selectedDisplay = state.displays[0]?.id || "main";
    renderDisplays();
    await loadPlaylist();
    renderLibrary();
  } catch (error) { notify(error.message, true); }
}
async function loadPlaylist() {
  state.playlist = await api("/api/admin/playlists/" + encodeURIComponent(state.selectedDisplay));
  renderPlaylist();
}
$("#display-select").addEventListener("change", async event => {
  state.selectedDisplay = event.target.value;
  renderDisplays();
  try { await loadPlaylist(); renderLibrary(); } catch (error) { notify(error.message, true); }
});
$("#refresh-btn").addEventListener("click", loadAll);
async function setDisplayMode(mode) {
  try {
    const result = await api("/api/admin/displays/" + encodeURIComponent(state.selectedDisplay) + "/control", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ mode })
    });
    $("#control-status").textContent = ({ play: "Playing", freeze: "Frozen", break: "Break screen" })[result.mode];
    notify("Display control: " + $("#control-status").textContent);
  } catch (error) { notify(error.message, true); }
}
$("#control-play").addEventListener("click", () => setDisplayMode("play"));
$("#control-freeze").addEventListener("click", () => setDisplayMode("freeze"));
$("#control-break").addEventListener("click", () => setDisplayMode("break"));
$("#display-form").addEventListener("submit", async event => {
  event.preventDefault();
  const name = $("#new-display-name").value.trim();
  const id = $("#new-display-id").value.trim();
  try {
    await api("/api/admin/displays", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id, name }) });
    state.selectedDisplay = id;
    $("#display-form").reset();
    await loadAll();
    notify("Display created. Player URL: " + location.origin + "/display/" + id);
  } catch (error) { notify(error.message, true); }
});
$("#upload-form").addEventListener("submit", async event => {
  event.preventDefault();
  const file = $("#media-file").files[0];
  if (!file) return;
  const button = event.currentTarget.querySelector("button[type=submit]");
  button.disabled = true; button.textContent = "Uploading…";
  $("#upload-status").textContent = "Uploading and processing " + file.name + "…";
  const form = new FormData();
  form.append("file", file);
  form.append("display_id", state.selectedDisplay);
  form.append("duration", $("#duration").value || "10");
  try {
    const result = await api("/api/admin/upload", { method: "POST", body: form });
    $("#upload-status").textContent = result.message;
    $("#upload-form").reset();
    $("#duration").value = "10";
    await loadAll();
    notify(result.message);
  } catch (error) {
    $("#upload-status").textContent = error.message;
    notify(error.message, true);
  } finally {
    button.disabled = false; button.textContent = "Upload to selected display ↗";
  }
});
$("#youtube-form").addEventListener("submit", async event => {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button[type=submit]");
  button.disabled = true; button.textContent = "Adding…";
  const form = new FormData();
  form.append("url", $("#youtube-url").value.trim());
  form.append("display_id", state.selectedDisplay);
  try {
    const result = await api("/api/admin/youtube", { method: "POST", body: form });
    $("#youtube-status").textContent = result.message;
    $("#youtube-form").reset();
    await loadAll();
    notify(result.message);
  } catch (error) {
    $("#youtube-status").textContent = error.message;
    notify(error.message, true);
  } finally {
    button.disabled = false; button.textContent = "Add YouTube to playlist ↗";
  }
});
$("#library").addEventListener("click", async event => {
  const add = event.target.closest(".add-media");
  const remove = event.target.closest(".delete-media");
  try {
    if (add) {
      const item = state.media.find(m => m.id === add.dataset.id);
      if (item && !state.playlist.some(p => p.id === item.id)) {
        state.playlist.push({ ...item, duration: Number($("#duration").value) || 10 });
        renderPlaylist(); renderLibrary();
      }
    }
    if (remove) {
      if (!confirm("Delete this asset from storage and every playlist?")) return;
      await api("/api/admin/media/" + encodeURIComponent(remove.dataset.id), { method: "DELETE" });
      await loadAll(); notify("Media deleted.");
    }
  } catch (error) { notify(error.message, true); }
});
$("#playlist").addEventListener("click", event => {
  const row = event.target.closest(".playlist-row");
  if (!row) return;
  const index = state.playlist.findIndex(item => item.id === row.dataset.id);
  if (event.target.closest(".remove-item")) state.playlist.splice(index, 1);
  else if (event.target.closest(".move-up") && index > 0) [state.playlist[index - 1], state.playlist[index]] = [state.playlist[index], state.playlist[index - 1]];
  else if (event.target.closest(".move-down") && index < state.playlist.length - 1) [state.playlist[index + 1], state.playlist[index]] = [state.playlist[index], state.playlist[index + 1]];
  renderPlaylist(); renderLibrary();
});
$("#save-playlist").addEventListener("click", async () => {
  try {
    await api("/api/admin/playlists/" + encodeURIComponent(state.selectedDisplay), {
      method: "PUT", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ media_ids: state.playlist.map(item => item.id), duration: Number($("#duration").value) || 10 })
    });
    await loadPlaylist(); notify("Playlist saved. The display will sync shortly.");
  } catch (error) { notify(error.message, true); }
});
$("#new-display-name").addEventListener("input", event => {
  const slug = event.target.value.toLowerCase().trim().replace(/[^a-z0-9_-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40);
  if (!$("#new-display-id").dataset.edited) $("#new-display-id").value = slug;
});
$("#new-display-id").addEventListener("input", event => { event.target.dataset.edited = "true"; });
loadAll();
