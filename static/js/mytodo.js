// Grab button once
const addTaskBtn = document.querySelector(".add-task-btn");

addTaskBtn.addEventListener("click", async () => {
  // Read inputs correctly
  const title = document.querySelector("#title").value.trim();
  const task = document.querySelector("#task").value.trim();
  const description = document.querySelector("#desc").value.trim();

  // Frontend validation
  if (!title || !task) {
    alert("Title and Task are required");
    return;
  }

  try {
    const res = await fetch("/api/add_task", {
      method: "POST",
      credentials: "include", // send session cookie
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        title: title,
        task: task,
        description: description
      })
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Failed to add task");
    }

    // Success
    clearInputs();
    loadTasks()
    console.log("Task added successfully");

  } catch (err) {
    console.error("Add task error:", err.message);
    alert(err.message);
  }
});

// Clear inputs correctly
function clearInputs() {
  document.querySelector("#title").value = "";
  document.querySelector("#task").value = "";
  document.querySelector("#desc").value = "";
}

async function loadTasks() {
  try {
    const res = await fetch("/api/show_task", {
      method: "GET",
      credentials: "include"
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Failed to fetch tasks");
    }

    renderTasks(data.tasks);

  } catch (err) {
    console.error(err.message);
  }
}

function renderTasks(tasks) {
  const list = document.querySelector(".todo-list");
  list.innerHTML = "";

  if (tasks.length === 0) {
    list.innerHTML = "<p>No tasks yet</p>";
    return;
  }

  tasks.forEach(t => {
    const div = document.createElement("div");
    div.className = "todo-item";
    div.innerHTML = `
      <h4>${t.title}</h4>
      <p>${t.task}</p>
      <small>${t.description}</small>
    `;
    list.appendChild(div);
  });
}

// Call on page load
loadTasks();

let logout = document.querySelector(".logout").addEventListener("click",()=>callAPI("/api/logout"))
function callAPI(url){
    fetch(url,{method:"POST"})
    .then(res => res.json())
    .then(data=>{
        if(data.success){
            window.location.href = data.redirect;
        }
    })
    .catch(err=>console.error(err))
}

todoList.addEventListener("click",async (e)=>{
  const btn = e.target.closest(".task-update-btn");
  if(!btn) return;
    const title = document.querySelector("#title").value.trim();
    const task = document.querySelector("#task").value.trim();
    const description = document.querySelector("#desc").value.trim();
    const taskId = btn.dataset.taskId;

    const payload = {}
    if(title !== "") payload.title = title;
    if(task !== "") payload.task = task;
    if(description !=="") payload.description = description;
    if(Object.keys(payload).length===0){
      alert("Enter atleast one field to update")
      return
    }
    console.log(taskId)
    console.log(payload)
    

    try{
      const res = await fetch(`/update-task/${taskId}`, {

        method: "PATCH",
        headers : {"Content-Type":"application/json"},
        body: JSON.stringify(payload)

      });
      const data = await res.json();
      if (data.success){
       clearInputs()
       await loadTasks();

      }
      else{
        alert(data.error)
        return;
      }
      
    }
    catch(err){
      console.log(err)
      alert("server error")
    
  }
})
