document.addEventListener('DOMContentLoaded', () => {
    // Global: Theme Toggle
    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const updateIcon = (isDark) => { if(themeIcon) themeIcon.textContent = isDark ? 'light_mode' : 'dark_mode'; };
    if (themeToggleBtn) {
        updateIcon(document.documentElement.classList.contains('dark'));
        themeToggleBtn.addEventListener('click', () => {
            document.documentElement.classList.toggle('dark');
            const isDark = document.documentElement.classList.contains('dark');
            localStorage.theme = isDark ? 'dark' : 'light';
            updateIcon(isDark);
        });
    }

    // Global: Sidebar Toggle (Desktop Chevron)
    const sidebarCollapseBtn = document.getElementById('sidebar-collapse-btn');
    const sidebarCollapseIcon = document.getElementById('sidebar-collapse-icon');
    
    if (sidebarCollapseBtn && sidebarCollapseIcon) {
        const updateSidebarIcon = (isCollapsed) => {
            sidebarCollapseIcon.textContent = isCollapsed ? 'chevron_right' : 'chevron_left';
        };

        // Initialize icon state
        updateSidebarIcon(document.documentElement.classList.contains('sidebar-collapsed'));

        sidebarCollapseBtn.addEventListener('click', () => {
            document.documentElement.classList.toggle('sidebar-collapsed');
            const isCollapsed = document.documentElement.classList.contains('sidebar-collapsed');
            localStorage.sidebarCollapsed = isCollapsed ? 'true' : 'false';
            updateSidebarIcon(isCollapsed);
        });
    }



    // Global: Logout Modal
    const logoutModal = document.getElementById('logout-modal');
    const cancelBtn = document.getElementById('cancel-logout');
    
    const showLogoutModal = (e) => {
        e.preventDefault();
        if (!logoutModal) return;
        logoutModal.classList.remove('hidden');
        void logoutModal.offsetWidth; // Force reflow
        logoutModal.classList.add('opacity-100');
        const modalDiv = logoutModal.querySelector('div');
        if (modalDiv) {
            modalDiv.classList.remove('scale-95');
            modalDiv.classList.add('scale-100');
        }
    };

    const hideLogoutModal = () => {
        if (!logoutModal) return;
        logoutModal.classList.remove('opacity-100');
        const modalDiv = logoutModal.querySelector('div');
        if (modalDiv) {
            modalDiv.classList.remove('scale-100');
            modalDiv.classList.add('scale-95');
        }
        setTimeout(() => {
            logoutModal.classList.add('hidden');
        }, 300);
    };

    document.addEventListener('click', (e) => {
        if (e.target.closest('.logout-trigger')) {
            showLogoutModal(e);
        }
    });

    if (cancelBtn) cancelBtn.addEventListener('click', hideLogoutModal);
    if (logoutModal) logoutModal.addEventListener('click', (e) => {
        if (e.target === logoutModal) hideLogoutModal();
    });

    // Global: disable autocomplete on all inputs
    document.querySelectorAll('input, textarea').forEach(el => {
        el.setAttribute('autocomplete', 'off');
    });

    // Global: Per-field edit unlock (used in settings/profiles)
    document.querySelectorAll('.edit-field-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const inputId = 'field-' + btn.dataset.target;
            const input = document.getElementById(inputId);
            if (!input) return;
            input.removeAttribute('readonly');
            input.classList.remove('cursor-default', 'select-none', 'opacity-70');
            input.classList.add('opacity-100');
            input.focus();
            btn.innerHTML = '<span class="material-symbols-outlined text-[14px] text-blue-500">check_circle</span><span class="text-blue-500">Editing</span>';
            btn.disabled = true;
        });
    });

    // Global: password visibility toggle
    document.querySelectorAll('input[type="password"]').forEach(input => {
        // Skip if already wrapped
        if (input.parentElement.classList.contains('pw-wrapper')) return;

        // Preserve original display style of parent
        const wrapper = document.createElement('div');
        wrapper.className = 'pw-wrapper';
        wrapper.style.cssText = 'position:relative; display:flex; align-items:center;';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);

        // Ensure input fills the wrapper
        input.style.flex = '1';
        input.style.minWidth = '0';
        input.style.paddingRight = '2.5rem';

        // Create the toggle button
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.style.cssText = 'position:absolute; right:0.75rem; top:50%; transform:translateY(-50%); display:flex; align-items:center; justify-content:center; background:none; border:none; cursor:pointer; padding:0; color:#94a3b8;';
        btn.innerHTML = '<span class="material-symbols-outlined" style="font-size:20px;line-height:1;">visibility</span>';
        wrapper.appendChild(btn);

        // Toggle logic
        btn.addEventListener('click', () => {
            const isHidden = input.type === 'password';
            input.type = isHidden ? 'text' : 'password';
            const icon = btn.querySelector('span');
            if (icon) icon.textContent = isHidden ? 'visibility_off' : 'visibility';
            btn.style.color = isHidden ? '#64748b' : '#94a3b8';
        });

        btn.addEventListener('mouseenter', () => btn.style.color = '#475569');
        btn.addEventListener('mouseleave', () => btn.style.color = input.type === 'text' ? '#64748b' : '#94a3b8');
    });

    // Global: real-time password strength checker
    const pwCheckTargets = ['new_password', 'password'];
    const rules = [
        { label: 'At least 8 characters',        test: v => v.length >= 8 },
        { label: 'One uppercase letter (A–Z)',    test: v => /[A-Z]/.test(v) },
        { label: 'One number (0–9)',              test: v => /\d/.test(v) },
        { label: 'One special character (!@#$%…)',test: v => /[!@#$%^&*()\-_=+\[\]{};':"\\|,.<>/?]/.test(v) },
    ];

    document.querySelectorAll('input[type="password"]').forEach(input => {
        if (!pwCheckTargets.includes(input.name)) return;

        // Build the checklist container
        const checker = document.createElement('div');
        checker.style.cssText = 'display:none; margin-top:8px; padding:10px 12px; border-radius:10px; background:rgba(248,250,252,0.9); border:1px solid #e2e8f0; font-size:11px; line-height:1.6;';
        checker.className = 'pw-checker';

        rules.forEach((rule, i) => {
            const row = document.createElement('div');
            row.id = `pw-rule-${input.name}-${i}`;
            row.style.cssText = 'display:flex; align-items:center; gap:6px; color:#94a3b8; transition:color 0.2s;';
            row.innerHTML = `<span class="material-symbols-outlined" style="font-size:14px;line-height:1;">radio_button_unchecked</span><span>${rule.label}</span>`;
            checker.appendChild(row);
        });

        const insertAfter = (el, ref) => ref.parentNode.insertBefore(el, ref.nextSibling);

        requestAnimationFrame(() => {
            const parent = input.closest('.pw-wrapper') || input.parentElement;
            if (parent) insertAfter(checker, parent);
        });

        const applyDark = () => {
            const dark = document.documentElement.classList.contains('dark');
            checker.style.background = dark ? 'rgba(22,27,34,0.95)' : 'rgba(248,250,252,0.9)';
            checker.style.borderColor = dark ? '#1d232c' : '#e2e8f0';
        };

        input.addEventListener('focus', () => { checker.style.display = 'block'; applyDark(); });
        input.addEventListener('blur', () => { if (!input.value) checker.style.display = 'none'; });

        input.addEventListener('input', () => {
            rules.forEach((rule, i) => {
                const row = checker.querySelector(`#pw-rule-${input.name}-${i}`);
                if (!row) return;
                const pass = rule.test(input.value);
                const icon = row.querySelector('span');
                if (icon) icon.textContent = pass ? 'check_circle' : 'radio_button_unchecked';
                row.style.color = pass ? '#22c55e' : '#94a3b8';
            });
        });

        const form = input.closest('form');
        if (form) {
            form.addEventListener('submit', (e) => {
                const allPass = rules.every(rule => rule.test(input.value));
                if (!allPass) {
                    e.preventDefault();
                    checker.style.display = 'block';
                    applyDark();
                    input.focus();
                }
            }, true);
        }
    });
});
