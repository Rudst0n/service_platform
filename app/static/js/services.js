document.addEventListener("DOMContentLoaded", () => {
    const inputs = document.querySelectorAll(".image-input");
    const progressBars = document.querySelectorAll(".progress-usage");

    inputs.forEach((input) => {
        input.addEventListener("change", function (event) {
            const serviceId = this.dataset.serviceId;
            const files = Array.from(event.target.files || []);

            renderPreview(serviceId, files);
        });
    });

    progressBars.forEach((bar) => {
        const percent = parseFloat(bar.dataset.usagePercent || "0");
        bar.style.width = `${percent}%`;
    });
});

function renderPreview(serviceId, files) {
    const container = document.getElementById(`preview-container-${serviceId}`);

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (!files.length) {
        container.innerHTML = `
            <div class="empty-preview">
                Nenhuma imagem selecionada.
            </div>
        `;
        return;
    }

    files.forEach((file) => {
        if (!file.type.startsWith("image/")) {
            return;
        }

        const reader = new FileReader();

        reader.onload = function (e) {
            const item = document.createElement("div");
            item.className = "preview-item";

            item.innerHTML = `
                <img src="${e.target.result}" alt="Pré visualização" class="preview-thumb">
            `;

            container.appendChild(item);
        };

        reader.readAsDataURL(file);
    });
}