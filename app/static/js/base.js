document.addEventListener("DOMContentLoaded", function () {
    const alerts = document.querySelectorAll(".app-alert");

    alerts.forEach((alert) => {
        setTimeout(() => {
            alert.style.transition = "opacity 0.4s ease, transform 0.4s ease";
            alert.style.opacity = "0";
            alert.style.transform = "translateY(-8px)";

            setTimeout(() => {
                alert.remove();
            }, 400);
        }, 1800);
    });
});