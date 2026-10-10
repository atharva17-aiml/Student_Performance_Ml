const container = document.getElementById('container');
document.getElementById('register').addEventListener('click', () => {
    container.classList.add("active");
});
document.getElementById('login').addEventListener('click', () => {
    container.classList.remove("active");
});
