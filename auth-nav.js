// SmartPick Hub - Professional Authentication Navigation

const smartPickNavClient = window.supabase.createClient(
    SUPABASE_URL,
    SUPABASE_PUBLISHABLE_KEY
);

function updateSmartPickNavigation(session) {
    const loginLink = document.getElementById("login-nav-link");
    const profileMenu = document.getElementById("profile-menu");

    const isLoggedIn = Boolean(session);

    if (loginLink) {
        loginLink.hidden = isLoggedIn;
    }

    if (profileMenu) {
        profileMenu.hidden = !isLoggedIn;
    }

    if (isLoggedIn && session.user) {
        const email = session.user.email || "";
        const displayName =
            session.user.user_metadata?.full_name ||
            session.user.user_metadata?.name ||
            email.split("@")[0] ||
            "Account";

        const initial = displayName.trim().charAt(0).toUpperCase() || "U";

        const nameElement = document.getElementById("profile-name");
        const avatarElement = document.getElementById("profile-avatar");
        const dropdownName = document.getElementById("profile-dropdown-name");
        const dropdownEmail = document.getElementById("profile-dropdown-email");

        if (nameElement) nameElement.textContent = displayName;
        if (avatarElement) avatarElement.textContent = initial;
        if (dropdownName) dropdownName.textContent = displayName;
        if (dropdownEmail) dropdownEmail.textContent = email;
    }
}

function closeProfileDropdown() {
    const trigger = document.getElementById("profile-trigger");
    const dropdown = document.getElementById("profile-dropdown");

    if (trigger && dropdown) {
        trigger.setAttribute("aria-expanded", "false");
        dropdown.hidden = true;
    }
}

function initializeProfileDropdown() {
    const trigger = document.getElementById("profile-trigger");
    const dropdown = document.getElementById("profile-dropdown");
    const logoutButton = document.getElementById("logout-nav-button");
    const profileMenu = document.getElementById("profile-menu");

    if (trigger && dropdown) {
        trigger.addEventListener("click", () => {
            const isOpen = trigger.getAttribute("aria-expanded") === "true";

            trigger.setAttribute("aria-expanded", String(!isOpen));
            dropdown.hidden = isOpen;
        });

        document.addEventListener("click", (event) => {
            if (profileMenu && !profileMenu.contains(event.target)) {
                closeProfileDropdown();
            }
        });

        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                closeProfileDropdown();
            }
        });
    }

    if (logoutButton) {
        logoutButton.addEventListener("click", async () => {
            logoutButton.disabled = true;
            logoutButton.textContent = "Logging out...";

            try {
                const { error } =
                    await smartPickNavClient.auth.signOut();

                if (error) throw error;

                window.location.replace("index.html");

            } catch (error) {
                console.error("Logout failed:", error.message);
                logoutButton.disabled = false;
                logoutButton.textContent = "Logout";
                alert("Logout failed. Please try again.");
            }
        });
    }
}

async function initializeSmartPickNavigation() {
    try {
        const { data, error } =
            await smartPickNavClient.auth.getSession();

        if (error) throw error;

        updateSmartPickNavigation(data.session);

    } catch (error) {
        console.error("Navigation session check failed:", error.message);
        updateSmartPickNavigation(null);
    }
}

smartPickNavClient.auth.onAuthStateChange(
    (event, session) => {
        updateSmartPickNavigation(session);
    }
);

initializeProfileDropdown();
initializeSmartPickNavigation();
