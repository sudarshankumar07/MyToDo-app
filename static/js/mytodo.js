const todoList = document.querySelector(".todo-list");
const addBtn = document.querySelector(".add-task-btn");


const titleInput = document.querySelector("#title");
const taskInput = document.querySelector("#task");
const descInput = document.querySelector("#desc");


// ---------- ADD ----------
addBtn.addEventListener("click", async () => {
  const title = titleInput.value.trim();
  const task = taskInput.value.trim();
  const desc = descInput.value.trim();

  if (!title || !task) return alert("Required");

  const res = await fetch("/api/add_task", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, task, description: desc })
  });

 if (res.ok) {
     clearInputs();
      loadTasks();
     
    }else{
      throw new Error(data.error || "Failed to add task");
    }
  
});

// ---------- LOAD ----------
async function loadTasks() {
  const res = await fetch("/api/show_task", {
    credentials: "include"
  });

  const data = await res.json();
  renderTasks(data.tasks);
}

// ---------- RENDER ----------
function renderTasks(tasks) {
  todoList.innerHTML = "";
  tasks.forEach(t => {
    todoList.innerHTML += `
      <div class="todo-item">
        <small>${t.created_at || ""}</small>
        <br>
        <h4>${t.title }</h4>
        <p>${t.task}</p>
        <small>${t.description || ""}</small>
        <br>
        <button type="button" class="task-del-btn" data-id="${t.id}">Delete</button>
        <button type="button" class="task-update-btn" data-id="${t.id}">Update</button>
      </div>`;
  });
}

// ---------- DELETE / UPDATE ----------
todoList.addEventListener("click", async e => {
  if (e.target.classList.contains("task-del-btn")) {
    await fetch("/delete-task", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: e.target.dataset.id })
    });
    loadTasks();
  }

  if (e.target.classList.contains("task-update-btn")) {
    const payload = {};
    if (titleInput.value) payload.title = titleInput.value;
    if (taskInput.value) payload.task = taskInput.value;
    if (descInput.value) payload.description = descInput.value;

    await fetch(`/update-task/${e.target.dataset.id}`, {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    clearInputs();
    await loadTasks();
  }
});

// ---------- LOGOUT ----------
document.querySelector(".logout").addEventListener("click", async () => {
  await fetch("/api/logout", {
    method: "POST",
    credentials: "include"
  });
  window.location.href = "/login_page";
});

loadTasks();







