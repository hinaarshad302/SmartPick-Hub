document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("newsletter-form");
    const emailInput = document.getElementById("newsletter-email");
    const submitButton = document.getElementById("newsletter-submit");
    const message = document.getElementById("newsletter-message");

    if (!form || !emailInput || !submitButton || !message) return;

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const apiBaseUrl = String(
            window.SMARTPICK_API_BASE_URL || ""
        ).trim().replace(/\/$/, "");

        if (!apiBaseUrl) {
            message.textContent =
                "Newsletter setup is not complete yet. Please try again later.";
            message.dataset.state = "error";
            return;
        }

        const email = emailInput.value.trim();
        if (!email) {
            emailInput.focus();
            return;
        }

        submitButton.disabled = true;
        submitButton.textContent = "Sending...";
        message.textContent = "Please wait while we send your confirmation email.";
        message.dataset.state = "pending";

        try {
            const response = await fetch(
                apiBaseUrl + "/newsletter/signup",
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email })
                }
            );

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                throw new Error(
                    data.detail ||
                    "We could not process your request. Please try again."
                );
            }

            message.textContent =
                data.message ||
                "Please check your inbox to confirm your subscription.";
            message.dataset.state = "success";
            form.reset();
        } catch (error) {
            message.textContent =
                error.message ||
                "The newsletter service is temporarily unavailable.";
            message.dataset.state = "error";
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = "Subscribe";
        }
    });
});
