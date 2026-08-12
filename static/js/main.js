document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) {
    window.lucide.createIcons();
  }

  const publicNav = document.querySelector("[data-public-nav]");
  const navToggle = document.querySelector("[data-nav-toggle]");
  if (publicNav) {
    const setNavState = () => publicNav.classList.toggle("is-scrolled", window.scrollY > 8);
    setNavState();
    window.addEventListener("scroll", setNavState, { passive: true });
  }
  if (publicNav && navToggle) {
    navToggle.addEventListener("click", () => {
      const isOpen = publicNav.classList.toggle("menu-open");
      navToggle.setAttribute("aria-expanded", String(isOpen));
    });
    publicNav.querySelectorAll("[data-nav-links] a").forEach((link) => {
      link.addEventListener("click", () => {
        publicNav.classList.remove("menu-open");
        navToggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  const appShell = document.querySelector(".app-shell");
  const sidebarToggle = document.querySelector("[data-sidebar-toggle]");
  if (appShell && sidebarToggle) {
    sidebarToggle.addEventListener("click", () => {
      const isCollapsed = appShell.classList.toggle("sidebar-collapsed");
      sidebarToggle.setAttribute("aria-label", isCollapsed ? "Expand navigation" : "Collapse navigation");
    });
  }

  const profileMenu = document.querySelector("[data-profile-menu]");
  const profileToggle = document.querySelector("[data-profile-toggle]");
  if (profileMenu && profileToggle) {
    profileToggle.addEventListener("click", () => {
      const isOpen = profileMenu.classList.toggle("is-open");
      profileToggle.setAttribute("aria-expanded", String(isOpen));
    });
    document.addEventListener("click", (event) => {
      if (!profileMenu.contains(event.target)) {
        profileMenu.classList.remove("is-open");
        profileToggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  document.querySelectorAll("[data-toggle-password]").forEach((button) => {
    const input = document.getElementById(button.dataset.togglePassword);
    if (!input) {
      return;
    }

    button.addEventListener("click", () => {
      const isHidden = input.type === "password";
      input.type = isHidden ? "text" : "password";
      button.textContent = isHidden ? "Hide" : "Show";
    });
  });

  document.querySelectorAll("[data-auth-notice]").forEach((button) => {
    button.addEventListener("click", () => {
      window.alert("Google Authentication will be available in the next version.");
    });
  });

  document.querySelectorAll("[data-reset-notice]").forEach((button) => {
    button.addEventListener("click", () => {
      window.alert("Password reset email service will be available in the next version.");
    });
  });

  document.querySelectorAll("[data-table-search]").forEach((input) => {
    const table = document.getElementById(input.dataset.tableSearch);
    if (!table) {
      return;
    }

    const rows = Array.from(table.querySelectorAll("tbody tr"));
    input.addEventListener("input", () => {
      const term = input.value.trim().toLowerCase();
      rows.forEach((row) => {
        row.hidden = term.length > 0 && !row.textContent.toLowerCase().includes(term);
      });
    });
  });
});
