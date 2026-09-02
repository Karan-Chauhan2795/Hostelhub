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
  const sidebarToggles = document.querySelectorAll("[data-sidebar-toggle]");
  if (appShell && sidebar && sidebarToggles.length) {
    const hoverPreviewQuery = window.matchMedia("(hover: hover) and (pointer: fine)");
    const mobileSidebarQuery = window.matchMedia("(max-width: 980px)");

    const updateSidebarToggles = () => {
      const isMobile = mobileSidebarQuery.matches;
      const isCollapsed = appShell.classList.contains("sidebar-collapsed");
      const isMobileOpen = appShell.classList.contains("sidebar-mobile-open");

      sidebarToggles.forEach((toggle) => {
        const isExpanded = isMobile ? isMobileOpen : !isCollapsed;
        toggle.setAttribute("aria-expanded", String(isExpanded));
        toggle.setAttribute("aria-label", isExpanded ? "Collapse navigation" : "Expand navigation");
      });
    };

    const setHoverPreview = (isActive) => {
      const canPreview = hoverPreviewQuery.matches && appShell.classList.contains("sidebar-collapsed");
      appShell.classList.toggle("sidebar-hover-preview", canPreview && isActive);
    };

    updateSidebarToggles();
    sidebarToggles.forEach((toggle) => {
      toggle.addEventListener("click", () => {
        if (mobileSidebarQuery.matches) {
          appShell.classList.toggle("sidebar-mobile-open");
        } else {
          appShell.classList.toggle("sidebar-collapsed");
          setHoverPreview(false);
        }
        updateSidebarToggles();
      });
    });

    sidebar.addEventListener("pointerenter", () => {
      if (!mobileSidebarQuery.matches) {
        setHoverPreview(true);
      }
    });
    sidebar.addEventListener("pointerleave", () => setHoverPreview(false));
    hoverPreviewQuery.addEventListener("change", () => setHoverPreview(false));
    mobileSidebarQuery.addEventListener("change", () => {
      appShell.classList.remove("sidebar-mobile-open");
      setHoverPreview(false);
      updateSidebarToggles();
    });
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

  const nova = document.querySelector("[data-nova]");
  if (nova) {
    const panel = nova.querySelector("[data-nova-panel]");
    const openButton = nova.querySelector("[data-nova-open]");
    const messages = nova.querySelector("[data-nova-messages]");
    const form = nova.querySelector("[data-nova-form]");
    const input = nova.querySelector("[data-nova-input]");
    const sendButton = nova.querySelector("[data-nova-send]");
    const storageKey = `hostelhub_nova_${nova.dataset.storageUser}`;
    let history = [];

    try { history = JSON.parse(window.localStorage.getItem(storageKey) || "[]"); } catch (_) { history = []; }
    if (!Array.isArray(history)) history = [];

    const renderMessage = (role, text, extraClass = "") => {
      const message = document.createElement("div");
      message.className = `nova-message is-${role}${extraClass ? ` ${extraClass}` : ""}`;
      message.textContent = text;
      messages.appendChild(message);
      messages.scrollTop = messages.scrollHeight;
    };
    const renderHistory = () => {
      messages.replaceChildren();
      if (!history.length) renderMessage("assistant", "Hi! I’m Nova. Ask me about HostelHub rooms, bookings, leave, notices or support.");
      history.forEach(({ role, text }) => renderMessage(role === "model" ? "assistant" : role, text));
    };
    const saveHistory = () => window.localStorage.setItem(storageKey, JSON.stringify(history.slice(-30)));
    const setNovaOpen = (isOpen) => {
      panel.hidden = !isOpen;
      openButton.hidden = isOpen;
      openButton.setAttribute("aria-expanded", String(isOpen));
      if (isOpen) {
        input.focus();
      } else {
        openButton.focus();
      }
    };
    const openNova = () => setNovaOpen(true);
    const closeNova = () => setNovaOpen(false);
    openButton.addEventListener("click", openNova);
    nova.querySelector("[data-nova-close]").addEventListener("click", (event) => {
      event.preventDefault();
      closeNova();
    });
    nova.querySelector("[data-nova-clear]").addEventListener("click", () => {
      if (window.confirm("Clear chat history?\n\nAre you sure you want to clear your Nova AI chat history? This action cannot be undone.")) {
        history = [];
        window.localStorage.removeItem(storageKey);
        renderHistory();
      }
    });
    document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !panel.hidden) closeNova(); });
    renderHistory();

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const text = input.value.trim();
      if (!text || sendButton.disabled) return;
      renderMessage("user", text);
      input.value = "";
      sendButton.disabled = true;
      renderMessage("assistant", "Nova is thinking…", "is-loading");
      const loading = messages.lastElementChild;
      try {
        const csrfToken = document.cookie.split("; ").find((cookie) => cookie.startsWith("csrftoken="))?.split("=")[1] || "";
        const response = await fetch(nova.dataset.endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRFToken": decodeURIComponent(csrfToken) },
          body: JSON.stringify({ message: text, history }),
        });
        const data = await response.json();
        loading.remove();
        if (!response.ok || !data.reply) throw new Error(data.error || "Nova is temporarily unavailable. Please try again shortly.");
        history.push({ role: "user", text }, { role: "model", text: data.reply });
        saveHistory();
        renderMessage("assistant", data.reply);
      } catch (error) {
        loading.remove();
        renderMessage("assistant", error.message || "Nova is temporarily unavailable. Please try again shortly.", "is-error");
      } finally {
        sendButton.disabled = false;
        input.focus();
      }
    });
  }
});
