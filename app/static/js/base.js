document.addEventListener("DOMContentLoaded", function () {
    setTimeout(function () {
        const alerts = document.querySelectorAll(".auto-alert");

        alerts.forEach(function (alert) {
            alert.style.transition = "opacity 0.5s ease";
            alert.style.opacity = "0";

            setTimeout(function () {
                alert.remove();
            }, 500);
        });
    }, 2000);
});