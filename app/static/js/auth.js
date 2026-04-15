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

    initPasswordRules();
    initPasswordToggle();
    initPasswordMatch();
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

function getPasswordChecks(password) {
    return {
        length: password.length >= 8,
        upper: /[A-Z]/.test(password),
        lower: /[a-z]/.test(password),
        number: /\d/.test(password),
        special: /[^A-Za-z0-9]/.test(password),
    };
}

function updatePasswordRules(passwordInput, rulesContainer) {
    if (!passwordInput || !rulesContainer) {
        return;
    }

    const checks = getPasswordChecks(passwordInput.value);

    rulesContainer.querySelectorAll(".password-rule").forEach((ruleItem) => {
        const ruleName = ruleItem.dataset.rule;
        const isValid = Boolean(checks[ruleName]);

        ruleItem.classList.toggle("is-valid", isValid);
        ruleItem.classList.toggle("is-invalid", !isValid);
    });
}

function initPasswordRules() {
    document.querySelectorAll("[data-password-rules]").forEach((rulesContainer) => {
        const inputId = rulesContainer.getAttribute("data-password-rules");
        const passwordInput = document.getElementById(inputId);

        if (!passwordInput) {
            return;
        }

        updatePasswordRules(passwordInput, rulesContainer);

        passwordInput.addEventListener("input", function () {
            updatePasswordRules(passwordInput, rulesContainer);
        });
    });
}

function initPasswordToggle() {
    document.querySelectorAll("[data-toggle-password]").forEach((button) => {
        button.addEventListener("click", function () {
            const inputId = button.getAttribute("data-toggle-password");
            const input = document.getElementById(inputId);

            if (!input) {
                return;
            }

            const eyeOpen = button.querySelector(".eye-open");
            const eyeClosed = button.querySelector(".eye-closed");

            if (input.type === "password") {
                input.type = "text";
                if (eyeOpen) eyeOpen.classList.add("d-none");
                if (eyeClosed) eyeClosed.classList.remove("d-none");
            } else {
                input.type = "password";
                if (eyeOpen) eyeOpen.classList.remove("d-none");
                if (eyeClosed) eyeClosed.classList.add("d-none");
            }
        });
    });
}

function initPasswordMatch() {
    const password = document.getElementById("password");
    const confirm = document.getElementById("confirm_password");
    const box = document.querySelector("[data-password-match]");

    if (!password || !confirm || !box) {
        return;
    }

    function validate() {
        const bothFilled = password.value.length > 0 && confirm.value.length > 0;
        const equal = bothFilled && password.value === confirm.value;

        box.classList.toggle("is-valid", equal);
        box.classList.toggle("is-invalid", !equal);
    }

    password.addEventListener("input", validate);
    confirm.addEventListener("input", validate);
    validate();
}