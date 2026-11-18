const resetClient = window.supabase.createClient(
    SUPABASE_URL,
    SUPABASE_PUBLISHABLE_KEY
);

const resetForm = document.getElementById("reset-password-form");
const resetSubmit = document.getElementById("reset-submit");
const resetMessage = document.getElementById("reset-message");
let recoverySessionReady = false;
let recoveryEventReceived = false;
const recoveryFlowDetected =
    new URLSearchParams(window.location.search).has("code") ||
    new URLSearchParams(window.location.hash.slice(1)).get("type") === "recovery";

async function checkRecoverySession() {
    if (!recoveryFlowDetected) {
        resetSubmit.disabled = true;
        resetMessage.textContent =
            "Open the password reset link from your email. If it has expired, request a new one.";
        return;
    }

    try {
        const { data, error } = await resetClient.auth.getSession();
        if (error) throw error;

        // A normal signed-in session is not proof of a password-recovery flow.
        // Only the PASSWORD_RECOVERY event below may authorize password changes.
        recoverySessionReady = recoveryEventReceived && Boolean(data.session);
        resetSubmit.disabled = !recoverySessionReady;

        resetMessage.textContent = recoverySessionReady
            ? "Your reset link is valid. You can now choose a new password."
            : "Please open the password reset link from your email. If it has expired, request a new one.";
    } catch (error) {
        resetSubmit.disabled = true;
        resetMessage.textContent =
            error?.message || "We could not verify this reset link. Please request a new one.";
    }
}

resetClient.auth.onAuthStateChange((event, session) => {
    if (event === "PASSWORD_RECOVERY" && recoveryFlowDetected) {
        recoveryEventReceived = true;
        recoverySessionReady = Boolean(session);
        resetSubmit.disabled = !recoverySessionReady;
        resetMessage.textContent = recoverySessionReady
            ? "Your reset link is valid. You can now choose a new password."
            : "This reset link is invalid or has expired. Please request a new one.";
    }
});

resetForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!recoverySessionReady) {
        resetMessage.textContent = "Please open a valid password reset link from your email.";
        return;
    }

    const password = document.getElementById("new-password").value;
    const confirmation = document.getElementById("confirm-new-password").value;

    if (password.length < 8) {
        resetMessage.textContent = "Password must be at least 8 characters long.";
        return;
    }

    if (password !== confirmation) {
        resetMessage.textContent = "The passwords do not match. Please try again.";
        return;
    }

    resetSubmit.disabled = true;
    resetMessage.textContent = "Updating your password...";

    try {
        const { error } = await resetClient.auth.updateUser({ password });
        if (error) throw error;

        resetMessage.textContent =
            "Your password has been updated. Please log in with your new password.";
        resetForm.reset();

        await resetClient.auth.signOut();
    } catch (error) {
        resetMessage.textContent =
            error?.message || "We could not update your password. Please try again.";
        resetSubmit.disabled = false;
    }
});

checkRecoverySession();
