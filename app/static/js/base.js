document.addEventListener("DOMContentLoaded", function () {

    document.querySelectorAll(".cpf-mask").forEach((input) => {
        input.addEventListener("input", () => {
            input.value = formatCPF(input.value);
        });

        input.value = formatCPF(input.value);
    });

    document.querySelectorAll(".cnpj-mask").forEach((input) => {
        input.addEventListener("input", () => {
            input.value = formatCNPJ(input.value);
        });

        input.value = formatCNPJ(input.value);
    });

    document.querySelectorAll(".phone-mask").forEach((input) => {
        input.addEventListener("input", () => {
            input.value = formatPhone(input.value);
        });

        input.value = formatPhone(input.value);
    });

});


function onlyDigits(value) {
    return (value || "").replace(/\D/g, "");
}


function formatCPF(value) {
    value = onlyDigits(value).slice(0, 11);

    if (value.length <= 3) {
        return value;
    }

    if (value.length <= 6) {
        return value.replace(/^(\d{3})(\d+)/, "$1.$2");
    }

    if (value.length <= 9) {
        return value.replace(/^(\d{3})(\d{3})(\d+)/, "$1.$2.$3");
    }

    return value.replace(/^(\d{3})(\d{3})(\d{3})(\d{1,2}).*/, "$1.$2.$3-$4");
}


function formatCNPJ(value) {
    value = onlyDigits(value).slice(0, 14);

    if (value.length <= 2) {
        return value;
    }

    if (value.length <= 5) {
        return value.replace(/^(\d{2})(\d+)/, "$1.$2");
    }

    if (value.length <= 8) {
        return value.replace(/^(\d{2})(\d{3})(\d+)/, "$1.$2.$3");
    }

    if (value.length <= 12) {
        return value.replace(/^(\d{2})(\d{3})(\d{3})(\d+)/, "$1.$2.$3/$4");
    }

    return value.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{1,2}).*/, "$1.$2.$3/$4-$5");
}


function formatPhone(value) {
    value = onlyDigits(value).slice(0, 11);

    if (value.length <= 2) {
        return value;
    }

    if (value.length <= 6) {
        return value.replace(/^(\d{2})(\d+)/, "($1) $2");
    }

    if (value.length <= 10) {
        return value.replace(/^(\d{2})(\d{4})(\d+)/, "($1) $2-$3");
    }

    return value.replace(/^(\d{2})(\d{5})(\d{4}).*/, "($1) $2-$3");
}