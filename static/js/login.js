// register = document.querySelector(".sign-btn")
// register.addEventListener("click",()=>callAPI("/api/register"))
// function callAPI(url){
//     fetch(url,{method:"POST"})
//     .then(res => res.json())
//     .then(data=>{
//         if(data.success){
//             window.location.href = data.redirect;
//         }
//     })
//     .catch(err=>console.error(err))
// }
login = document.querySelector(".login-btn")

login.addEventListener("click",async()=>{
    const email = document.querySelector(".email").value;
    const password = document.querySelector(".pass").value;
    if(!email || !password){
        alert("All Fields Requiered")
        return
    }
    fetch("/user-login",{
        method:"POST",
        credentials: "include",
        headers:{
            "Content-Type":"application/json"
        },
        body: JSON.stringify({
            email:email,
            password:password
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
        // ✅ REAL redirect
        window.location.href = data.redirect;
        } else {
        alert(data.message);
        }
    })

})



