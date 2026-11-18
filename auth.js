const supabaseClient = window.supabase.createClient(
    SUPABASE_URL,
    SUPABASE_PUBLISHABLE_KEY
);

const authForm = document.getElementById("auth-form");
const authTitle = document.getElementById("auth-title");
const authDescription = document.getElementById("auth-description");
const authSubmit = document.getElementById("auth-submit");
const authSwitch = document.getElementById("auth-switch");
const authSwitchText = document.getElementById("auth-switch-text");
const authMessage = document.getElementById("auth-message");
const forgotPasswordButton = document.getElementById("forgot-password");
const consentGroup = document.getElementById("auth-consent-group");
const consentInput = document.getElementById("auth-consent");

const passwordInput = document.getElementById("auth-password");
const confirmGroup = document.getElementById("confirm-password-group");
const confirmInput = document.getElementById("auth-confirm-password");

let isSignup = false;

function updateAuthMode() {
    authTitle.textContent = isSignup ? "Create Account" : "Welcome Back";

    authDescription.textContent = isSignup
        ? "Create your SmartPick Hub account."
        : "Login to your SmartPick Hub account.";

    authSubmit.textContent = isSignup ? "Sign Up" : "Login";

    authSwitchText.textContent = isSignup
        ? "Already have an account?"
        : "Don't have an account?";

    authSwitch.textContent = isSignup ? "Login" : "Sign Up";

    confirmGroup.hidden = !isSignup;
    confirmInput.required = isSignup;

    consentGroup.hidden = !isSignup;
    consentInput.required = isSignup;
    consentInput.checked = false;

    passwordInput.autocomplete = isSignup
        ? "new-password"
        : "current-password";

    authMessage.textContent = "";
}

forgotPasswordButton.addEventListener("click", async () => {
    if (isSignup) {
        isSignup = false;
        authForm.reset();
        updateAuthMode();
    }

    const email = document.getElementById("auth-email").value.trim();
    if (!email) {
        authMessage.textContent = "Enter your account email first, then select Forgot password.";
        document.getElementById("auth-email").focus();
        return;
    }

    forgotPasswordButton.disabled = true;
    authMessage.textContent = "Sending password reset email...";

    try {
        const { error } = await supabaseClient.auth.resetPasswordForEmail(email, {
            redirectTo: new URL("reset-password.html", window.location.href).href
        });

        if (error) throw error;
        authMessage.textContent =
            "If an account exists for this email, a password reset link will be sent. Please check your inbox.";
    } catch (error) {
        authMessage.textContent =
            error?.message || "We could not send the reset email. Please try again.";
    } finally {
        forgotPasswordButton.disabled = false;
    }
});

authSwitch.addEventListener("click", () => {
    isSignup = !isSignup;
    authForm.reset();
    updateAuthMode();
});

document.querySelectorAll(".password-toggle").forEach(button => {
    button.addEventListener("click", () => {
        const input = document.getElementById(button.dataset.target);
        const showing = input.type === "text";

        input.type = showing ? "password" : "text";
        button.textContent = showing ? "Show" : "Hide";
        button.setAttribute(
            "aria-label",
            showing ? "Show password" : "Hide password"
        );
    });
});

authForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("auth-email").value.trim();
    const password = passwordInput.value;

    if (!email) {
        authMessage.textContent = "Please enter your email address.";
        return;
    }

    if (password.length < 8) {
        authMessage.textContent = "Password must be at least 8 characters long.";
        return;
    }

    if (isSignup && password !== confirmInput.value) {
        authMessage.textContent = "Passwords do not match. Please try again.";
        return;
    }

    if (isSignup && !consentInput.checked) {
        authMessage.textContent =
            "Please agree to the Terms of Use and review the Privacy Policy before creating an account.";
        consentInput.focus();
        return;
    }

    const submittingSignup = isSignup;
    authSubmit.disabled = true;
    authSwitch.disabled = true;
    authMessage.textContent = "Please wait...";

    try {
        if (submittingSignup) {
            const { data, error } = await supabaseClient.auth.signUp({
                email,
                password,
                options: {
                    emailRedirectTo: new URL("profile.html", window.location.href).href
                }
            });

            if (error) throw error;

            if (data.session) {
                authMessage.textContent = "Account created successfully! Opening your profile...";
                window.location.replace("profile.html");
            } else {
                authMessage.textContent =
                    "Account created! Please check your email to verify your account before logging in.";
            }

        } else {
            const { error } = await supabaseClient.auth.signInWithPassword({
                email,
                password
            });

            if (error) throw error;

            authMessage.textContent = "Login successful! Opening your profile...";
            window.location.replace("profile.html");
        }

    } catch (error) {
        authMessage.textContent =
            error?.message || "We could not complete your request. Please try again.";
    } finally {
        authSubmit.disabled = false;
        authSwitch.disabled = false;
    }
});

updateAuthMode();
