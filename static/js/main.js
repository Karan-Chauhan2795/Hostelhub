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
  const sidebar = document.querySelector("[data-sidebar]");
  const sidebarToggle = document.querySelector("[data-sidebar-toggle]");
  if (appShell && sidebar && sidebarToggle) {
    const hoverPreviewQuery = window.matchMedia("(hover: hover) and (pointer: fine)");

    const updateSidebarToggle = (isCollapsed) => {
      sidebarToggle.setAttribute("aria-expanded", String(!isCollapsed));
      sidebarToggle.setAttribute("aria-label", isCollapsed ? "Expand navigation" : "Collapse navigation");
    };

    const setHoverPreview = (isActive) => {
      const canPreview = hoverPreviewQuery.matches && appShell.classList.contains("sidebar-collapsed");
      appShell.classList.toggle("sidebar-hover-preview", canPreview && isActive);
    };

    updateSidebarToggle(appShell.classList.contains("sidebar-collapsed"));
    sidebarToggle.addEventListener("click", () => {
      const isCollapsed = appShell.classList.toggle("sidebar-collapsed");
      setHoverPreview(false);
      updateSidebarToggle(isCollapsed);
    });

    sidebar.addEventListener("pointerenter", () => setHoverPreview(true));
    sidebar.addEventListener("pointerleave", () => setHoverPreview(false));
    hoverPreviewQuery.addEventListener("change", () => setHoverPreview(false));
  }

  const logoutModal = document.querySelector("[data-logout-modal]");
  const logoutTriggers = document.querySelectorAll("[data-logout-trigger]");
  if (logoutModal && logoutTriggers.length) {
    const dialog = logoutModal.querySelector("[role='dialog']");
    const cancelButton = logoutModal.querySelector("[data-logout-cancel]");
    const focusableSelector = "button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex='-1'])";
    let lastFocusedElement = null;

    const closeLogoutModal = () => {
      logoutModal.hidden = true;
      if (lastFocusedElement) {
        lastFocusedElement.focus();
      }
    };

    const openLogoutModal = (trigger) => {
      lastFocusedElement = trigger;
      logoutModal.hidden = false;
      requestAnimationFrame(() => cancelButton.focus());
    };

    logoutTriggers.forEach((trigger) => {
      trigger.addEventListener("click", () => openLogoutModal(trigger));
    });
    cancelButton.addEventListener("click", closeLogoutModal);
    logoutModal.addEventListener("click", (event) => {
      if (event.target === logoutModal) {
        closeLogoutModal();
      }
    });
    document.addEventListener("keydown", (event) => {
      if (logoutModal.hidden) {
        return;
      }
      if (event.key === "Escape") {
        event.preventDefault();
        closeLogoutModal();
        return;
      }
      if (event.key === "Tab") {
        const focusableElements = Array.from(dialog.querySelectorAll(focusableSelector));
        const firstElement = focusableElements[0];
        const lastElement = focusableElements.at(-1);
        if (!firstElement || !lastElement) {
          return;
        }
        if (event.shiftKey && document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        } else if (!event.shiftKey && document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
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
