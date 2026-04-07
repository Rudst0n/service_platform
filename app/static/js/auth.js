document.addEventListener("DOMContentLoaded", function () {
    const cpfInput = document.getElementById("cpf");
    const cnpjInput = document.getElementById("cnpj");
    const loginInput = document.getElementById("login");

    if (cpfInput) {
        cpfInput.addEventListener("input", function (e) {
            e.target.value = formatCPF(e.target.value);
        });

        cpfInput.value = formatCPF(cpfInput.value);
    }

    if (cnpjInput) {
        cnpjInput.addEventListener("input", function (e) {
            e.target.value = formatCNPJ(e.target.value);
        });

        cnpjInput.value = formatCNPJ(cnpjInput.value);
    }

    if (loginInput) {
        loginInput.addEventListener("input", function (e) {
            const value = e.target.value;

            if (/[a-zA-Z@]/.test(value)) {
                return;
            }

            e.target.value = formatCPF(value);
        });

        loginInput.value = formatCPF(loginInput.value);
    }
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