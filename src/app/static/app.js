const api = {
  async get(path) {
    const res = await fetch(path);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async post(path, body) {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body ?? {}),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async del(path) {
    const res = await fetch(path, { method: "DELETE" });
    if (!res.ok) throw new Error(await res.text());
    return res.text();
  },
};

const state = {
  participants: [],
  trips: [],
  activeUser: null,
  activeTripId: null,
};

function setStatus(msg, isError = false) {
  const el = document.getElementById("status");
  el.textContent = msg;
  el.style.color = isError ? "#c00" : "#1f1f1f";
}

async function loadParticipants() {
  state.participants = await api.get("/participants/");
  const select = document.getElementById("user-select");
  const assign = document.getElementById("participant-assign");
  const delSel = document.getElementById("participant-delete");
  select.innerHTML = "";
  assign.innerHTML = "";
  delSel.innerHTML = "";
  state.participants.forEach((p) => {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.textContent = p.name;
    assign.appendChild(opt.cloneNode(true));
    delSel.appendChild(opt);
  });
  renderParticipants();
  refreshUserSelect();
}

async function loadTrips() {
  state.trips = await api.get("/trips/");
  const sel = document.getElementById("trip-select");
  sel.innerHTML = "";
  if (!state.trips.length) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "No trips yet";
    sel.appendChild(opt);
    setActiveTrip(null);
    return;
  }

  state.trips.forEach((t) => {
    const opt = document.createElement("option");
    opt.value = t.id;
    opt.textContent = t.name;
    sel.appendChild(opt);
  });

  const keepCurrent = state.activeTripId && state.trips.some((t) => t.id === state.activeTripId);
  const nextTripId = keepCurrent ? state.activeTripId : state.trips[0].id;
  setActiveTrip(nextTripId);
}

function currentTrip() {
  return state.trips.find((t) => t.id === state.activeTripId) || null;
}

function tripParticipants() {
  const trip = currentTrip();
  return trip ? trip.participants : [];
}

function setActiveTrip(tripId) {
  state.activeTripId = tripId;
  const sel = document.getElementById("trip-select");
  if (sel) sel.value = tripId || "";
  renderTripDetails();
  renderParticipants();
  renderTasks();
  renderProposals();
  updateTripDependentVisibility();
  refreshUserSelect();
}

function updateTripDependentVisibility() {
  const hasTrip = Boolean(state.activeTripId && currentTrip());
  document.querySelectorAll(".trip-dependent").forEach((el) => {
    el.classList.toggle("hidden", !hasTrip);
  });
  if (!hasTrip) {
    document.getElementById("tasks-list").innerHTML = "";
    document.getElementById("proposals-list").innerHTML = "";
    document.getElementById("trip-details").textContent = "Select a trip to manage it.";
  }
}

function renderParticipants() {
  const list = document.getElementById("participants-list");
  list.innerHTML = "";
  const trip = currentTrip();
  const items = trip ? trip.participants : state.participants;
  items.forEach((p) => {
    const li = document.createElement("li");
    li.className = "list-item";
    const actions = [];
    if (trip) {
      actions.push(`<button onclick="removeParticipantFromTrip('${p.id}')">Remove from trip</button>`);
    }
    actions.push(`<button onclick="deleteUserById('${p.id}')">Delete user</button>`);
    li.innerHTML = `
      <span>${p.name}</span>
      <span class="badge">${p.id.slice(0, 8)}</span>
      <span class="row">${actions.join(" ")}</span>`;
    list.appendChild(li);
  });
}

function renderTripDetails() {
  const trip = currentTrip();
  const container = document.getElementById("trip-details");
  if (!trip) {
    container.textContent = "Select a trip to manage it.";
    return;
  }
  container.innerHTML = `
    <div><strong>${trip.name}</strong> (${trip.start_date} → ${trip.end_date})</div>
    <div class="muted">Participants: ${trip.participants.map((p) => p.name).join(", ") || "None"}</div>
  `;
}

function requireUser() {
  if (!state.activeUser) {
    setStatus("Select or create a user first", true);
    return false;
  }
  return true;
}

function requireTrip() {
  if (!state.activeTripId || !currentTrip()) {
    setStatus("Select a trip first", true);
    return false;
  }
  return true;
}

async function addUser() {
  const name = document.getElementById("new-user-name").value.trim();
  if (!name) return setStatus("Enter a name", true);
  await api.post("/participants/", { name });
  document.getElementById("new-user-name").value = "";
  await loadParticipants();
  setStatus("Participant added");
}

async function addTrip() {
  const name = document.getElementById("trip-name").value.trim();
  const start = document.getElementById("trip-start").value;
  const end = document.getElementById("trip-end").value;
  if (!name || !start || !end) return setStatus("Trip name, start, end required", true);
  await api.post("/trips/", { name, start_date: start, end_date: end });
  document.getElementById("trip-name").value = "";
  document.getElementById("trip-start").value = "";
  document.getElementById("trip-end").value = "";
  await loadTrips();
  setStatus("Trip added");
}

async function assignParticipant() {
  if (!requireTrip()) return;
  const tripId = state.activeTripId;
  const participantId = document.getElementById("participant-assign").value;
  if (!tripId || !participantId) return setStatus("Select trip and participant", true);
  await api.post(`/trips/${tripId}/participants/${participantId}`);
  await loadTrips();
  setStatus("Participant assigned to trip");
}

async function addTask() {
  if (!requireUser() || !requireTrip()) return;
  const tripId = state.activeTripId;
  const desc = document.getElementById("task-desc").value.trim();
  if (!tripId || !desc) return setStatus("Select trip and enter task", true);
  await api.post(`/trips/${tripId}/tasks/`, { description: desc, participant_id: state.activeUser });
  document.getElementById("task-desc").value = "";
  await refreshTrip(tripId);
  setStatus("Task added");
}

async function toggleDone(taskId, done) {
  if (!requireUser() || !requireTrip()) return;
  const tripId = state.activeTripId;
  await api.post(`/trips/${tripId}/tasks/${taskId}/done?done=${done}`, { participant_id: state.activeUser });
  await refreshTrip(tripId);
  setStatus(done ? "Task marked done" : "Task reopened");
}

async function deleteTask(taskId) {
  if (!requireUser() || !requireTrip()) return;
  const tripId = state.activeTripId;
  await api.del(`/trips/${tripId}/tasks/${taskId}?participant_id=${state.activeUser}`);
  await refreshTrip(tripId);
  setStatus("Task removed");
}

async function addProposal() {
  if (!requireUser() || !requireTrip()) return;
  const tripId = state.activeTripId;
  const title = document.getElementById("proposal-title").value.trim();
  const description = document.getElementById("proposal-desc").value.trim();
  if (!tripId || !title) return setStatus("Select trip and enter a title", true);
  await api.post(`/trips/${tripId}/proposals/`, {
    title,
    description,
    participant_id: state.activeUser,
  });
  document.getElementById("proposal-title").value = "";
  document.getElementById("proposal-desc").value = "";
  await refreshTrip(tripId);
  setStatus("Proposal added");
}

async function upvoteProposal(proposalId) {
  if (!requireUser() || !requireTrip()) return;
  const tripId = state.activeTripId;
  await api.post(`/trips/${tripId}/proposals/${proposalId}/upvote`, { participant_id: state.activeUser });
  await refreshTrip(tripId);
  setStatus("Proposal upvoted");
}

async function deleteProposal(proposalId) {
  if (!requireUser() || !requireTrip()) return;
  const tripId = state.activeTripId;
  await api.del(`/trips/${tripId}/proposals/${proposalId}?participant_id=${state.activeUser}`);
  await refreshTrip(tripId);
  setStatus("Proposal deleted");
}

async function refreshTrip(tripId) {
  const trip = await api.get(`/trips/${tripId}`);
  const idx = state.trips.findIndex((t) => t.id === tripId);
  if (idx >= 0) state.trips[idx] = trip;
  setActiveTrip(tripId);
}

async function deleteTrip() {
  if (!state.activeTripId) return setStatus("Select a trip to delete", true);
  await api.del(`/trips/${state.activeTripId}`);
  state.activeTripId = null;
  await loadTrips();
  setStatus("Trip deleted");
}

async function deleteUser() {
  const sel = document.getElementById("participant-delete");
  const participantId = sel.value;
  if (!participantId) return setStatus("Select a user to delete", true);
  await deleteUserById(participantId);
}

async function deleteUserById(participantId) {
  await api.del(`/participants/${participantId}`);
  if (state.activeUser === participantId) state.activeUser = null;
  await loadParticipants();
  await loadTrips();
  setStatus("Participant deleted");
}

async function removeParticipantFromTrip(participantId) {
  if (!requireTrip()) return;
  const tripId = state.activeTripId;
  await api.del(`/trips/${tripId}/participants/${participantId}`);
  if (state.activeUser === participantId) state.activeUser = null;
  await loadTrips();
  setStatus("Participant removed from trip");
}

function renderTasks() {
  const trip = currentTrip();
  const list = document.getElementById("tasks-list");
  list.innerHTML = "";
  if (!trip) return;
  trip.tasks.forEach((task) => {
    const li = document.createElement("li");
    li.className = "list-item";
    const done = task.done ? "✓" : "";
    li.innerHTML = `
      <span>${done ? `<strong>${done}</strong> ` : ""}${task.description} <span class="muted">by ${task.participant_id.slice(0, 8)}</span></span>
      <span class="row">
        <button onclick="toggleDone('${task.id}', true)" ${task.done ? "disabled" : ""}>Mark done</button>
        <button onclick="toggleDone('${task.id}', false)" ${!task.done ? "disabled" : ""}>Reopen</button>
        <button onclick="deleteTask('${task.id}')">Delete</button>
      </span>`;
    list.appendChild(li);
  });
}

function renderProposals() {
  const trip = currentTrip();
  const list = document.getElementById("proposals-list");
  list.innerHTML = "";
  if (!trip) return;
  trip.proposals.forEach((p) => {
    const votes = p.upvotes ? p.upvotes.length : 0;
    const li = document.createElement("li");
    li.className = "list-item";
    li.innerHTML = `
      <span><strong>${p.title}</strong> — ${p.description || ""} <span class="badge">votes: ${votes}</span></span>
      <span class="row">
        <button onclick="upvoteProposal('${p.id}')">Upvote</button>
        <button onclick="deleteProposal('${p.id}')">Delete</button>
      </span>`;
    list.appendChild(li);
  });
}

function wireEvents() {
  document.getElementById("user-select").addEventListener("change", (e) => {
    state.activeUser = e.target.value;
  });
  document.getElementById("create-user-btn").addEventListener("click", () => {
    document.getElementById("new-user-name").focus();
  });
  document.getElementById("add-user").addEventListener("click", () =>
    handleAction(addUser)
  );
  document.getElementById("delete-user").addEventListener("click", () =>
    handleAction(deleteUser)
  );
  document.getElementById("add-trip").addEventListener("click", () =>
    handleAction(addTrip)
  );
  document.getElementById("delete-trip").addEventListener("click", () =>
    handleAction(deleteTrip)
  );
  document.getElementById("assign-participant").addEventListener("click", () =>
    handleAction(assignParticipant)
  );
  document.getElementById("trip-select").addEventListener("change", (e) => {
    setActiveTrip(e.target.value || null);
  });
  document.getElementById("add-task").addEventListener("click", () =>
    handleAction(addTask)
  );
  document.getElementById("add-proposal").addEventListener("click", () =>
    handleAction(addProposal)
  );
}

async function handleAction(fn) {
  try {
    setStatus("Working...");
    await fn();
  } catch (err) {
    console.error(err);
    setStatus(err.message || "Request failed", true);
  }
}

function refreshUserSelect() {
  const select = document.getElementById("user-select");
  select.innerHTML = "";
  const members = tripParticipants();
  if (!members.length) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "No participants in trip";
    select.appendChild(opt);
    state.activeUser = null;
    return;
  }

  members.forEach((p) => {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.textContent = p.name;
    select.appendChild(opt);
  });

  const keepCurrent = state.activeUser && members.some((p) => p.id === state.activeUser);
  state.activeUser = keepCurrent ? state.activeUser : members[0].id;
  select.value = state.activeUser;
}

(async function init() {
  wireEvents();
  try {
    await loadParticipants();
    await loadTrips();
    setStatus("Ready.");
  } catch (err) {
    setStatus(err.message || "Initialization failed", true);
  }
})();
