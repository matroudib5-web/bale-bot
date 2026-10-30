document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll('.btn');

    buttons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const action = e.target.getAttribute('data-action');
            
            // اینجا بعدا متن های هرکدوم رو مینویسی
            let message = "";
            switch(action) {
                case "assassin":
                    message = "Contract request sent. We will find you.";
                    break;
                case "drugs":
                    message = "Supply ordered. Delivery in 3 days.";
                    break;
                case "skin":
                    message = "Redirecting to the leather collection...";
                    break;
                case "organs":
                    message = "Organ reserved. Awaiting extraction.";
                    break;
                case "citizenship":
                    message = "US citizenship purchased. Welcome.";
                    break;
                case "identity":
                    message = "Dossier acquired. They are watching you.";
                    break;
                case "hack":
                    message = "Initiating breach... (Just kidding).";
                    break;
                default:
                    message = "Action completed.";
            }
            alert(message);
        });
    });
});
