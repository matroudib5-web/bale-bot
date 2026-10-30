document.addEventListener("DOMContentLoaded", () => {
    const langToggle = document.getElementById("lang-toggle");
    const textElements = document.querySelectorAll("[data-en]");
    let currentLang = 'en';

    // عملکرد دکمه‌های خرید
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            if (currentLang === 'en') {
                alert("Action pending. Wait for my order.");
            } else {
                alert("عملیات در انتظار. منتظر دستور من باش.");
            }
        });
    });

    // عملکرد تغییر زبان
    langToggle.addEventListener("click", () => {
        if (currentLang === 'en') {
            currentLang = 'fa';
            langToggle.innerText = "EN";
            textElements.forEach(el => {
                el.innerText = el.getAttribute("data-fa");
                el.classList.add("fa-text");
            });
            // تغییر فونت کل صفحه به فارسی
            document.body.style.fontFamily = "Tahoma, sans-serif"; 
        } else {
            currentLang = 'en';
            langToggle.innerText = "FA";
            textElements.forEach(el => {
                el.innerText = el.getAttribute("data-en");
                el.classList.remove("fa-text");
            });
            // برگردوندن فونت به هکری
            document.body.style.fontFamily = "'Share Tech Mono', monospace";
        }
    });
});
