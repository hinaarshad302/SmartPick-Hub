document.addEventListener("DOMContentLoaded", function () {

  console.log("SmartPick Hub loaded successfully!");

  // Automatic copyright year
  const copyright = document.querySelector(".footer-bottom p:first-child");

  if (copyright) {
    copyright.textContent = "© " + new Date().getFullYear() +
      " SmartPick Hub. All rights reserved.";
  }

  // Mobile navigation
  const menuToggle = document.getElementById("menu-toggle");
  const siteNav = document.getElementById("site-nav");

  if (menuToggle && siteNav) {

    menuToggle.addEventListener("click", function () {

      const isOpen = siteNav.classList.toggle("menu-open");

      menuToggle.setAttribute("aria-expanded", String(isOpen));

      menuToggle.setAttribute(
        "aria-label",
        isOpen ? "Close navigation menu" : "Open navigation menu"
      );

      const menuIcon = menuToggle.querySelector(".menu-icon");

      if (menuIcon) {
        menuIcon.textContent = isOpen ? "✕" : "☰";
      }

    });

    // Close menu after selecting a navigation link
    siteNav.querySelectorAll("a").forEach(function (link) {

      link.addEventListener("click", function () {

        siteNav.classList.remove("menu-open");

        menuToggle.setAttribute("aria-expanded", "false");
        menuToggle.setAttribute("aria-label", "Open navigation menu");

        const menuIcon = menuToggle.querySelector(".menu-icon");

        if (menuIcon) {
          menuIcon.textContent = "☰";
        }

      });

    });

  }

});
