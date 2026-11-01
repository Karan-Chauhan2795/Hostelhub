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

  const notificationsMenu = document.querySelector("[data-notifications-menu]");
  const notificationsToggle = document.querySelector("[data-notifications-toggle]");
  if (notificationsMenu && notificationsToggle) {
    const badge = notificationsMenu.querySelector(".notification-badge");
    const countPill = notificationsMenu.querySelector(".count-pill");
    const userId = notificationsMenu.dataset.userId || "anon";
    const rawIds = (notificationsMenu.dataset.noticeIds || "").trim();
    const noticeIds = rawIds ? rawIds.split(",").map((s) => parseInt(s.trim(), 10)).filter((n) => !isNaN(n)) : [];
    const latestId = parseInt(notificationsMenu.dataset.latestId || "0", 10);

    // User-specific seen records
    const storageKey = `hostelhub_user_${userId}_last_seen_notice_id`;
    const lastSeenId = parseInt(localStorage.getItem(storageKey) || "0", 10);

    // Calculate how many notices in the list have pk > lastSeenId
    const unreadCount = noticeIds.filter((id) => id > lastSeenId).length;

    const updateBadgeUI = (count) => {
      if (count > 0) {
        if (badge) {
          badge.textContent = String(count);
          badge.style.display = "";
        }
        if (countPill) {
          countPill.textContent = `${count} new`;
          countPill.style.display = "";
        }
      } else {
        if (badge) {
          badge.style.display = "none";
        }
        if (countPill) {
          countPill.style.display = "none";
        }
      }
    };

    const markNoticesAsSeen = () => {
      if (latestId > 0) {
        localStorage.setItem(storageKey, String(latestId));
      }
      updateBadgeUI(0);
    };

    // If currently on notice list or detail page, mark as seen for this user
    const isNoticePage = window.location.pathname.startsWith("/notices/");
    if (isNoticePage) {
      markNoticesAsSeen();
    } else {
      updateBadgeUI(unreadCount);
    }

    notificationsToggle.addEventListener("click", () => {
      const isOpen = notificationsMenu.classList.toggle("is-open");
      notificationsToggle.setAttribute("aria-expanded", String(isOpen));
      if (isOpen) {
        markNoticesAsSeen();
      }
    });

    document.addEventListener("click", (event) => {
      if (!notificationsMenu.contains(event.target)) {
        notificationsMenu.classList.remove("is-open");
        notificationsToggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  const calendarMenu = document.querySelector("[data-calendar-menu]");
  const calendarToggle = document.querySelector("[data-calendar-toggle]");
  if (calendarMenu && calendarToggle) {
    calendarToggle.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = calendarMenu.classList.toggle("is-open");
      calendarToggle.setAttribute("aria-expanded", String(isOpen));
    });

    document.addEventListener("click", (event) => {
      if (!calendarMenu.contains(event.target)) {
        calendarMenu.classList.remove("is-open");
        calendarToggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  // Smooth Calendar Day Switching (prevents page refresh and scrolling to bottom)
  // ==========================================
  // Smooth Calendar & Schedule Interaction (AJAX)
  // Prevents full page reloads and scroll jumps
  // ==========================================
  const calendarCards = document.querySelectorAll("[data-calendar-card]");
  const calendarRibbons = document.querySelectorAll("[data-calendar-ribbon]");

  // Helper to rebind day clicks on a container
  function bindCalendarDays(container, onDateSelect) {
    container.querySelectorAll("[data-calendar-day]").forEach((dayBtn) => {
      dayBtn.onclick = (e) => {
        e.preventDefault();
        const dateStr = dayBtn.dataset.date;
        if (dateStr) onDateSelect(dateStr);
      };
    });
  }

  // Dashboard Calendar Cards (Student, Warden, Admin)
  calendarCards.forEach((card) => {
    const apiUrl = card.dataset.apiUrl;
    const titleEl = card.querySelector("[data-calendar-selected-title]");
    const monthYearEl = card.querySelector("[data-calendar-month-year]");
    const daysContainer = card.querySelector("[data-calendar-days-container]");
    const nextEventContainer = card.querySelector("[data-calendar-next-event-container]");
    const footerLink = card.querySelector("[data-calendar-footer-link]");
    const viewAllLink = card.querySelector("[data-calendar-viewall-link]");
    const prevBtn = card.querySelector('[data-calendar-nav="prev"]');
    const todayBtn = card.querySelector('[data-calendar-nav="today"]');
    const nextBtn = card.querySelector('[data-calendar-nav="next"]');
    const readinessTitle = document.querySelector("[data-readiness-title]");
    const readinessList = document.querySelector("[data-readiness-list]");

    if (!apiUrl) return;

    let currentPrevWeek = prevBtn ? new URL(prevBtn.href, window.location.origin).searchParams.get("date") : "";
    let currentNextWeek = nextBtn ? new URL(nextBtn.href, window.location.origin).searchParams.get("date") : "";

    async function loadDate(dateStr) {
      if (!dateStr) return;

      // Update URL query string in browser without reload or scrolling
      const currentUrl = new URL(window.location);
      currentUrl.searchParams.set("date", dateStr);
      window.history.replaceState({}, "", currentUrl);

      try {
        const resp = await fetch(`${apiUrl}?date=${encodeURIComponent(dateStr)}`);
        if (!resp.ok) return;
        const data = await resp.json();

        // 1. Update Month / Year
        if (monthYearEl && data.calendar_month_year) {
          monthYearEl.textContent = data.calendar_month_year;
        }

        // 2. Update Nav Buttons
        if (prevBtn && data.prev_week_str) {
          prevBtn.href = `?date=${data.prev_week_str}`;
          currentPrevWeek = data.prev_week_str;
        }
        if (todayBtn && data.today_str) {
          todayBtn.href = `?date=${data.today_str}`;
        }
        if (nextBtn && data.next_week_str) {
          nextBtn.href = `?date=${data.next_week_str}`;
          currentNextWeek = data.next_week_str;
        }

        // 3. Update Days Row
        if (daysContainer && data.week_days) {
          daysContainer.innerHTML = data.week_days
            .map((day) => {
              const selClass = day.is_selected ? "is-selected" : "";
              const todayClass = day.is_today ? "today" : "";
              const dotHtml = day.has_event ? '<span class="day-dot"></span>' : "";
              return `
                <a href="?date=${day.date_str}" data-calendar-day data-date="${day.date_str}" class="calendar-day-btn ${selClass} ${todayClass}" title="${day.date_str}">
                  <span>${day.day_number}</span>
                  ${dotHtml}
                </a>
              `;
            })
            .join("");
          bindCalendarDays(daysContainer, loadDate);
        } else {
          // Fallback: update active class on existing buttons
          card.querySelectorAll("[data-calendar-day]").forEach((b) => {
            b.classList.toggle("is-selected", b.dataset.date === data.selected_date_str);
          });
        }

        // 4. Update Header Titles & Links
        if (titleEl) {
          titleEl.textContent = `Schedule · ${data.selected_date_formatted}`;
        }
        if (footerLink) {
          footerLink.href = `/events/?date=${data.selected_date_str}`;
        }
        if (viewAllLink) {
          viewAllLink.href = `/events/?date=${data.selected_date_str}`;
        }

        // 5. Update Next Event / Highlight Card
        if (nextEventContainer) {
          if (data.next_event) {
            const ev = data.next_event;
            let iconClass = "fa-regular fa-calendar-check";
            if (ev.event_type === "DINNER") iconClass = "fa-solid fa-utensils";
            else if (ev.event_type === "MEETING") iconClass = "fa-solid fa-users";
            else if (ev.event_type === "MAINTENANCE") iconClass = "fa-solid fa-screwdriver-wrench";
            else if (ev.event_type === "SPORTS") iconClass = "fa-solid fa-volleyball";
            else if (ev.event_type === "CELEBRATION") iconClass = "fa-solid fa-cake-candles";

            const recurringBadge = ev.is_recurring_daily
              ? `<span class="status-badge badge-warning" style="font-size: 9.5px; padding: 2px 7px;">Daily</span>`
              : "";
            const datePrefix = data.is_today ? "Today" : data.selected_date_formatted;
            const descHtml = ev.description
              ? `<span class="event-inline-desc">${ev.description}</span>`
              : "";

            nextEventContainer.innerHTML = `
              <div class="next-event next-event-interactive" style="cursor: pointer;" data-href="/events/?date=${data.selected_date_str}" title="Click to view in Event Management">
                <i class="${iconClass}"></i>
                <div>
                  <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
                    <strong>${ev.title}</strong>
                    ${recurringBadge}
                  </div>
                  <small>${datePrefix} · ${ev.time} · ${ev.location}</small>
                  ${descHtml}
                </div>
              </div>
            `;
          } else {
            nextEventContainer.innerHTML = `
              <div class="next-event next-event-empty">
                <i class="fa-regular fa-circle-check" style="background:#ecfdf5; color:#059669;"></i>
                <div>
                  <strong>No events on this day</strong>
                  <small>${data.selected_date_full}</small>
                </div>
              </div>
            `;
          }
        }

        // 6. Update Warden Readiness Section & Student Events Section
        const wardenFullAgendaBtn = document.querySelector("[data-warden-full-agenda-btn]");
        if (wardenFullAgendaBtn) {
          wardenFullAgendaBtn.href = `/events/?date=${data.selected_date_str}`;
        }
        if (readinessTitle) {
          readinessTitle.textContent = `Agenda for ${data.selected_date_formatted}`;
        }

        // Student Schedule Section
        const studentEventsTitle = document.querySelector("[data-student-events-title]");
        const studentFullEventsBtn = document.querySelector("[data-student-full-events-btn]");
        const studentEventsList = document.querySelector("[data-student-events-list]");
        if (studentEventsTitle) {
          studentEventsTitle.textContent = `Events for ${data.selected_date_formatted}`;
        }
        if (studentFullEventsBtn) {
          studentFullEventsBtn.href = `/events/?date=${data.selected_date_str}`;
        }

        const renderEventsHtml = (events) => {
          if (!events || events.length === 0) {
            return `
              <li class="empty-activity-notice">
                <span class="activity-icon" style="background:#f1f5f9; color:#94a3b8;"><i class="fa-regular fa-circle-check"></i></span>
                <span><strong>No events scheduled for this day</strong><small>Routine hostel schedule & activities.</small></span>
              </li>
            `;
          }
          return events
            .map((ev) => {
              let iconClass = "fa-regular fa-calendar-check";
              let iconColor = "readiness-icon-teal";
              if (ev.event_type === "DINNER") {
                iconClass = "fa-solid fa-utensils";
                iconColor = "readiness-icon-orange";
              } else if (ev.event_type === "MEETING") {
                iconClass = "fa-solid fa-users";
                iconColor = "readiness-icon-blue";
              } else if (ev.event_type === "MAINTENANCE") {
                iconClass = "fa-solid fa-screwdriver-wrench";
              } else if (ev.event_type === "SPORTS") {
                iconClass = "fa-solid fa-volleyball";
              } else if (ev.event_type === "CELEBRATION") {
                iconClass = "fa-solid fa-cake-candles";
              }

              const badge = ev.is_recurring_daily
                ? `<span class="status-badge badge-warning" style="font-size: 10px; padding: 2px 7px;"><i class="fa-solid fa-repeat" style="font-size: 8px; margin-right: 3px;"></i>Daily</span>`
                : `<span class="status-badge badge-info" style="font-size: 10px; padding: 2px 7px;">${ev.event_type_display}</span>`;

              const audienceBadge = ev.audience === "WARDEN_ONLY"
                ? `<span class="badge-audience-warden"><i class="fa-solid fa-user-shield"></i> Warden Only</span>`
                : (ev.audience === "ALL" && !data.is_student
                    ? `<span class="badge-audience-all"><i class="fa-solid fa-users"></i> All</span>`
                    : "");

              const desc = ev.description
                ? `<p class="readiness-desc">${ev.description}</p>`
                : "";

              return `
                <li class="readiness-item-wrap">
                  <div class="readiness-item" style="cursor: pointer;" data-href="/events/?date=${data.selected_date_str}" title="Click to view in Event Management">
                    <span class="readiness-icon ${iconColor}">
                      <i class="${iconClass}"></i>
                    </span>
                    <div class="readiness-details">
                      <div class="readiness-title-row">
                        <strong>${ev.title}</strong>
                      </div>
                      <div class="readiness-tags-row">
                        ${audienceBadge}
                        ${badge}
                      </div>
                      <div class="readiness-meta">
                        <span><i class="fa-regular fa-clock"></i> ${ev.time}</span>
                        <span><i class="fa-solid fa-location-dot"></i> ${ev.location}</span>
                      </div>
                      ${desc}
                    </div>
                  </div>
                </li>
              `;
            })
            .join("");
        };

        if (readinessList) {
          readinessList.innerHTML = renderEventsHtml(data.events);
        }
        if (studentEventsList) {
          studentEventsList.innerHTML = renderEventsHtml(data.events);
        }

        // 7. Update Admin Controls Events List (if on Admin dashboard)
        const adminEventsTitle = document.querySelector("[data-admin-events-title]");
        const adminAddBtn = document.querySelector("[data-admin-add-event-btn]");
        const adminFullCalBtn = document.querySelector("[data-admin-full-cal-btn]");
        const adminEventsList = document.querySelector("[data-admin-events-list]");
        if (adminEventsTitle) {
          adminEventsTitle.textContent = `Events for ${data.selected_date_formatted}`;
        }
        if (adminAddBtn) {
          adminAddBtn.href = `/events/create/?date=${data.selected_date_str}`;
        }
        if (adminFullCalBtn) {
          adminFullCalBtn.href = `/events/?date=${data.selected_date_str}`;
        }
        if (adminEventsList) {
          if (data.events && data.events.length > 0) {
            adminEventsList.innerHTML = data.events
              .map((ev) => {
                let iconClass = "fa-regular fa-calendar-check";
                let iconColor = "readiness-icon-teal";
                if (ev.event_type === "DINNER") {
                  iconClass = "fa-solid fa-utensils";
                  iconColor = "readiness-icon-orange";
                } else if (ev.event_type === "MEETING") {
                  iconClass = "fa-solid fa-users";
                  iconColor = "readiness-icon-blue";
                } else if (ev.event_type === "MAINTENANCE") {
                  iconClass = "fa-solid fa-screwdriver-wrench";
                } else if (ev.event_type === "SPORTS") {
                  iconClass = "fa-solid fa-volleyball";
                } else if (ev.event_type === "CELEBRATION") {
                  iconClass = "fa-solid fa-cake-candles";
                }

                const badge = ev.is_recurring_daily
                  ? `<span class="status-badge badge-warning" style="font-size: 10px; padding: 2px 7px;"><i class="fa-solid fa-repeat" style="font-size: 8px; margin-right: 3px;"></i>Daily</span>`
                  : `<span class="status-badge badge-info" style="font-size: 10px; padding: 2px 7px;">${ev.event_type_display}</span>`;

                const audienceBadge = ev.audience === "WARDEN_ONLY"
                  ? `<span class="badge-audience-warden"><i class="fa-solid fa-user-shield"></i> Warden Only</span>`
                  : `<span class="badge-audience-all"><i class="fa-solid fa-users"></i> All</span>`;

                const desc = ev.description
                  ? `<p class="readiness-desc">${ev.description}</p>`
                  : "";

                return `
                  <li class="readiness-item-wrap">
                    <div class="readiness-item" style="cursor: pointer;" data-href="/events/?date=${data.selected_date_str}" title="Click to view in Event Management">
                      <span class="readiness-icon ${iconColor}">
                        <i class="${iconClass}"></i>
                      </span>
                      <div class="readiness-details" style="flex: 1;">
                        <div class="readiness-title-row">
                          <strong>${ev.title}</strong>
                          <a href="/events/${ev.id}/edit/?date=${data.selected_date_str}" class="action-btn action-btn-edit" title="Edit this event" onclick="event.stopPropagation();"><i class="fa-regular fa-pen-to-square"></i> Edit</a>
                        </div>
                        <div class="readiness-tags-row">
                          ${audienceBadge}
                          ${badge}
                        </div>
                        <div class="readiness-meta">
                          <span><i class="fa-regular fa-clock"></i> ${ev.time}</span>
                          <span><i class="fa-solid fa-location-dot"></i> ${ev.location}</span>
                        </div>
                        ${desc}
                      </div>
                    </div>
                  </li>
                `;
              })
              .join("");
          } else {
            adminEventsList.innerHTML = `
              <li class="empty-activity-notice" style="padding: 24px 16px; text-align: center;">
                <span class="activity-icon" style="background:#f1f5f9; color:#94a3b8;"><i class="fa-regular fa-circle-check"></i></span>
                <span><strong>No events scheduled for this day</strong><small>Click 'Add Event' to publish a new activity on this date.</small></span>
              </li>
            `;
          }
        }
      } catch (err) {
        console.error("Failed to load events for date:", err);
      }
    }

    // Attach week nav buttons
    if (prevBtn) {
      prevBtn.addEventListener("click", (e) => {
        e.preventDefault();
        if (currentPrevWeek) loadDate(currentPrevWeek);
      });
    }
    if (todayBtn) {
      todayBtn.addEventListener("click", (e) => {
        e.preventDefault();
        const todayStr = new URL(todayBtn.href, window.location.origin).searchParams.get("date");
        if (todayStr) loadDate(todayStr);
      });
    }
    if (nextBtn) {
      nextBtn.addEventListener("click", (e) => {
        e.preventDefault();
        if (currentNextWeek) loadDate(currentNextWeek);
      });
    }

    // Attach initial day click listeners
    if (daysContainer) {
      bindCalendarDays(daysContainer, loadDate);
    } else {
      bindCalendarDays(card, loadDate);
    }
  });

  // Calendar Ribbon on the Events Page (/events/)
  calendarRibbons.forEach((ribbon) => {
    const apiUrl = ribbon.dataset.apiUrl;
    const monthYearEl = ribbon.querySelector("[data-calendar-month-year]");
    const selectedFullEl = ribbon.querySelector("[data-calendar-selected-full]");
    const weekStrip = ribbon.querySelector("[data-calendar-week-strip]");
    const prevBtn = ribbon.querySelector('[data-calendar-nav="prev"]');
    const todayBtn = ribbon.querySelector('[data-calendar-nav="today"]');
    const nextBtn = ribbon.querySelector('[data-calendar-nav="next"]');

    const dayHeading = document.querySelector("[data-events-selected-heading]");
    const addBtn = document.querySelector("[data-events-add-btn]");
    const timeline = document.querySelector("[data-events-timeline]");

    if (!apiUrl) return;

    let currentPrevWeek = prevBtn ? new URL(prevBtn.href, window.location.origin).searchParams.get("date") : "";
    let currentNextWeek = nextBtn ? new URL(nextBtn.href, window.location.origin).searchParams.get("date") : "";

    async function loadRibbonDate(dateStr) {
      if (!dateStr) return;

      const currentUrl = new URL(window.location);
      currentUrl.searchParams.set("date", dateStr);
      window.history.replaceState({}, "", currentUrl);

      try {
        const resp = await fetch(`${apiUrl}?date=${encodeURIComponent(dateStr)}`);
        if (!resp.ok) return;
        const data = await resp.json();

        // 1. Update Month / Year and Header
        if (monthYearEl && data.calendar_month_year) {
          monthYearEl.textContent = data.calendar_month_year;
        }
        if (selectedFullEl && data.selected_date_full) {
          selectedFullEl.textContent = data.selected_date_full;
        }

        // 2. Update Nav Buttons
        if (prevBtn && data.prev_week_str) {
          prevBtn.href = `?date=${data.prev_week_str}`;
          currentPrevWeek = data.prev_week_str;
        }
        if (todayBtn && data.today_str) {
          todayBtn.href = `?date=${data.today_str}`;
        }
        if (nextBtn && data.next_week_str) {
          nextBtn.href = `?date=${data.next_week_str}`;
          currentNextWeek = data.next_week_str;
        }

        // 3. Update Week Strip Days
        if (weekStrip && data.week_days) {
          weekStrip.innerHTML = data.week_days
            .map((day) => {
              const selClass = day.is_selected ? "is-selected" : "";
              const todayClass = day.is_today ? "is-today" : "";
              const dotHtml = day.has_event ? '<span class="day-dot"></span>' : "";
              return `
                <a href="?date=${day.date_str}" data-calendar-day data-date="${day.date_str}" class="week-strip-day ${selClass} ${todayClass}">
                  <span class="day-label">${day.label}</span>
                  <span class="day-num">${day.day_number}</span>
                  ${dotHtml}
                </a>
              `;
            })
            .join("");
          bindCalendarDays(weekStrip, loadRibbonDate);
        }

        // 4. Update Highlight Section Header
        if (dayHeading) {
          const todayBadge = data.is_today
            ? '<span class="status-badge badge-info" style="font-size: 11px; margin-left: 6px;">Today</span>'
            : "";
          dayHeading.innerHTML = `${data.selected_date_full} ${todayBadge}`;
        }
        if (addBtn) {
          addBtn.href = `/events/create/?date=${data.selected_date_str}`;
        }

        // 5. Update Timeline
        if (timeline) {
          if (data.events && data.events.length > 0) {
            timeline.innerHTML = data.events
              .map((ev) => {
                let iconClass = "fa-regular fa-calendar-check";
                if (ev.event_type === "DINNER") iconClass = "fa-solid fa-utensils";
                else if (ev.event_type === "MEETING") iconClass = "fa-solid fa-users";
                else if (ev.event_type === "MAINTENANCE") iconClass = "fa-solid fa-screwdriver-wrench";
                else if (ev.event_type === "SPORTS") iconClass = "fa-solid fa-volleyball";
                else if (ev.event_type === "CELEBRATION") iconClass = "fa-solid fa-cake-candles";

                const badge = ev.is_recurring_daily
                  ? '<span class="status-badge badge-warning" title="Standard daily scheduled event"><i class="fa-solid fa-repeat" style="font-size: 9px; margin-right: 3px;"></i>Daily dinner</span>'
                  : `<span class="status-badge badge-info">${ev.event_type_display}</span>`;

                const audienceBadge = ev.audience === "WARDEN_ONLY"
                  ? '<span class="status-badge" style="background: #fdf2f8; color: #db2777; border: 1px solid #fbcfe8; font-size: 10px; padding: 2px 7px;"><i class="fa-solid fa-user-shield" style="font-size: 8px; margin-right: 3px;"></i>Warden Only</span>'
                  : (!data.is_student ? '<span class="status-badge" style="background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; font-size: 10px; padding: 2px 7px;"><i class="fa-solid fa-users" style="font-size: 8px; margin-right: 3px;"></i>All</span>' : '');

                const recurringClass = ev.is_recurring_daily ? "event-recurring" : "";
                const organizer = ev.created_by
                  ? `<span><i class="fa-solid fa-user-shield"></i> ${ev.created_by}</span>`
                  : "";
                const descHtml = ev.description ? `<p class="event-desc">${ev.description}</p>` : "";

                let adminActions = "";
                if (data.is_admin) {
                  const deleteBtn = !ev.is_recurring_daily
                    ? `<a href="/events/${ev.id}/delete/?date=${data.selected_date_str}" class="action-btn action-btn-delete" title="Delete event"><i class="fa-regular fa-trash-can"></i></a>`
                    : "";
                  adminActions = `
                    <div class="event-item-actions">
                      <a href="/events/${ev.id}/edit/?date=${data.selected_date_str}" class="action-btn action-btn-edit" title="Edit this event"><i class="fa-regular fa-pen-to-square"></i> Edit</a>
                      ${deleteBtn}
                    </div>
                  `;
                }

                return `
                  <div class="event-timeline-item ${recurringClass}">
                    <div class="event-time-badge" style="width: auto; min-width: 78px; padding: 8px 10px;">
                      <i class="${iconClass}"></i>
                      <span>${ev.time}</span>
                    </div>
                    <div class="event-info">
                      <div class="event-title-row">
                        <h4>${ev.title}</h4>
                        <div class="event-badges">${audienceBadge}${badge}</div>
                      </div>
                      <p class="event-meta">
                        <span><i class="fa-solid fa-location-dot"></i> ${ev.location}</span>
                        ${organizer}
                      </p>
                      ${descHtml}
                    </div>
                    ${adminActions}
                  </div>
                `;
              })
              .join("");
          } else {
            const addAction = data.is_admin
              ? `<a href="/events/create/?date=${data.selected_date_str}" class="btn-micro btn-micro-outline" style="margin-top: 8px;">Schedule an event</a>`
              : "";
            timeline.innerHTML = `
              <div class="empty-events-box">
                <i class="fa-regular fa-calendar-check" style="font-size: 32px; color: #94a3b8; margin-bottom: 8px;"></i>
                <p>No special events scheduled for this day.</p>
                ${addAction}
              </div>
            `;
          }
        }
      } catch (err) {
        console.error("Failed to load events for ribbon date:", err);
      }
    }

    if (prevBtn) {
      prevBtn.addEventListener("click", (e) => {
        e.preventDefault();
        if (currentPrevWeek) loadRibbonDate(currentPrevWeek);
      });
    }
    if (todayBtn) {
      todayBtn.addEventListener("click", (e) => {
        e.preventDefault();
        const todayStr = new URL(todayBtn.href, window.location.origin).searchParams.get("date");
        if (todayStr) loadRibbonDate(todayStr);
      });
    }
    if (nextBtn) {
      nextBtn.addEventListener("click", (e) => {
        e.preventDefault();
        if (currentNextWeek) loadRibbonDate(currentNextWeek);
      });
    }

    if (weekStrip) {
      bindCalendarDays(weekStrip, loadRibbonDate);
    }
  });

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
    const confirmation = nova.querySelector("[data-nova-confirm]");
    const clearButton = nova.querySelector("[data-nova-clear]");
    const cancelClearButton = nova.querySelector("[data-nova-confirm-cancel]");
    const confirmClearButton = nova.querySelector("[data-nova-confirm-clear]");
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
      if (!history.length) renderMessage("assistant", "Hi! I’m Nova. Ask me about HostelHub rooms, bookings, leave, notices or complaints.");
      history.forEach(({ role, text }) => renderMessage(role === "model" ? "assistant" : role, text));
    };
    const saveHistory = () => window.localStorage.setItem(storageKey, JSON.stringify(history.slice(-30)));
    const setNovaOpen = (isOpen, shouldFocus = true) => {
      panel.hidden = !isOpen;
      openButton.hidden = isOpen;
      openButton.setAttribute("aria-expanded", String(isOpen));
      if (isOpen && shouldFocus) {
        input.focus();
      } else if (!isOpen && shouldFocus) {
        openButton.focus();
      }
    };
    const openNova = () => setNovaOpen(true);
    const closeNova = () => setNovaOpen(false);
    const closeConfirmation = () => { confirmation.hidden = true; };
    openButton.addEventListener("click", openNova);
    nova.querySelector("[data-nova-close]").addEventListener("click", (event) => {
      event.preventDefault();
      closeNova();
    });
    clearButton.addEventListener("click", () => {
      confirmation.hidden = false;
      cancelClearButton.focus();
    });
    cancelClearButton.addEventListener("click", closeConfirmation);
    confirmClearButton.addEventListener("click", () => {
      history = [];
      window.localStorage.removeItem(storageKey);
      renderHistory();
      closeConfirmation();
    });
    confirmation.addEventListener("click", (event) => { if (event.target === confirmation) closeConfirmation(); });
    document.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      if (!confirmation.hidden) closeConfirmation();
      else if (!panel.hidden) closeNova();
    });
    renderHistory();
    setNovaOpen(false, false);

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

  // Warden checklist interaction and daily state persistence
  const checklistCard = document.querySelector("[data-warden-checklist]");
  if (checklistCard) {
    const checklistDate = checklistCard.dataset.checklistDate || new Date().toISOString().split("T")[0];
    const storageKey = `hostelhub_warden_checklist_${checklistDate}`;
    const items = checklistCard.querySelectorAll(".checklist-interactive li[data-check-id]");
    const countBadge = checklistCard.querySelector("[data-checklist-count]");

    const updateChecklistUI = (checkedSet) => {
      let doneCount = 0;
      items.forEach((item) => {
        const id = item.dataset.checkId;
        const isDone = checkedSet.has(id);
        if (isDone) {
          doneCount++;
          item.classList.add("done");
          const icon = item.querySelector("i");
          if (icon) {
            icon.className = "fa-solid fa-check";
          }
        } else {
          item.classList.remove("done");
          const icon = item.querySelector("i");
          if (icon) {
            icon.className = "";
          }
        }
      });
      if (countBadge) {
        countBadge.textContent = `${doneCount} / ${items.length}`;
      }
    };

    let savedChecked;
    try {
      const stored = window.localStorage.getItem(storageKey);
      if (stored !== null) {
        savedChecked = new Set(JSON.parse(stored));
      }
    } catch {
      savedChecked = null;
    }

    if (!savedChecked) {
      // Initialize from default HTML markup
      savedChecked = new Set();
      items.forEach((item) => {
        if (item.classList.contains("done")) {
          savedChecked.add(item.dataset.checkId);
        }
      });
      try {
        window.localStorage.setItem(storageKey, JSON.stringify(Array.from(savedChecked)));
      } catch {}
    }

    updateChecklistUI(savedChecked);

    items.forEach((item) => {
      const toggleCheck = () => {
        const id = item.dataset.checkId;
        if (savedChecked.has(id)) {
          savedChecked.delete(id);
        } else {
          savedChecked.add(id);
        }
        try {
          window.localStorage.setItem(storageKey, JSON.stringify(Array.from(savedChecked)));
        } catch {}
        updateChecklistUI(savedChecked);
      };

      item.addEventListener("click", toggleCheck);
      item.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          toggleCheck();
        }
      });
    });
  }

  // Global delegation for interactive cards with data-href
  document.addEventListener("click", (e) => {
    // If the click happened on an interactive button, edit link, or any anchor, let its default/own handler work
    if (e.target.closest(".action-btn, button, input, select, textarea") || (e.target.closest("a") && !e.target.closest("[data-href]"))) {
      return;
    }
    const clickableCard = e.target.closest("[data-href]");
    if (clickableCard && clickableCard.dataset.href) {
      // If clicking inside an anchor tag directly, avoid duplicate navigation
      if (e.target.closest("a")) return;
      window.location.href = clickableCard.dataset.href;
    }
  });
});

