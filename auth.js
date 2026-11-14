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

    passwordInput.autocomplete = isSignup
        ? "new-password"
        : "current-password";

    authMessage.textContent = "";
}

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

    if (isSignup && password !== confirmInput.value) {
        authMessage.textContent = "Passwords do not match. Please try again.";
        return;
    }

    authSubmit.disabled = true;
    authMessage.textContent = "Please wait...";

    try {
        if (isSignup) {
            const { data, error } = await supabaseClient.auth.signUp({
                email,
                password,
                options: {
                    emailRedirectTo: window.location.origin + "/index.html"
                }
            });

            if (error) throw error;

            authMessage.textContent = data.session
                ? "Account created successfully!"
                : "Account created! Please check your email to verify your account.";

        } else {
            const { error } = await supabaseClient.auth.signInWithPassword({
                email,
                password
            });

            if (error) throw error;

            authMessage.textContent = "Login successful! Opening your profile...";
            window.location.href = "index.html";
        }

    } catch (error) {
        authMessage.textContent = error.message;
    } finally {
        authSubmit.disabled = false;
    }
});

updateAuthMode();
