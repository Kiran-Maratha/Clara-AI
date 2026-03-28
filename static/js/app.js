document.addEventListener('DOMContentLoaded', () => {
    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const updateIcon = (isDark) => { if (themeIcon) themeIcon.textContent = isDark ? 'light_mode' : 'dark_mode'; };
    
    // Manages the global light/dark theme persistence and icon state.
    if (themeToggleBtn) {
        updateIcon(document.documentElement.classList.contains('dark'));
        themeToggleBtn.addEventListener('click', () => {
            document.documentElement.classList.toggle('dark');
            const isDark = document.documentElement.classList.contains('dark');
            localStorage.theme = isDark ? 'dark' : 'light';
            updateIcon(isDark);
        });
    }

    const sidebarCollapseBtn = document.getElementById('sidebar-collapse-btn');
    const sidebarCollapseIcon = document.getElementById('sidebar-collapse-icon');

    // Controls the collapsible state of the navigation sidebar for desktop layouts.
    if (sidebarCollapseBtn && sidebarCollapseIcon) {
        const updateSidebarIcon = (isCollapsed) => {
            sidebarCollapseIcon.textContent = isCollapsed ? 'chevron_right' : 'chevron_left';
        };

        updateSidebarIcon(document.documentElement.classList.contains('sidebar-collapsed'));

        sidebarCollapseBtn.addEventListener('click', () => {
            document.documentElement.classList.toggle('sidebar-collapsed');
            const isCollapsed = document.documentElement.classList.contains('sidebar-collapsed');
            localStorage.sidebarCollapsed = isCollapsed ? 'true' : 'false';
            updateSidebarIcon(isCollapsed);
        });
    }

    const logoutModal = document.getElementById('logout-modal');
    const cancelBtn = document.getElementById('cancel-logout');
    const removePicModal = document.getElementById('remove-pic-modal');
    const cancelRemovePicBtn = document.getElementById('cancel-remove-pic');
    const confirmRemovePicBtn = document.getElementById('confirm-remove-pic');

    const deleteAccountModal = document.getElementById('delete-account-modal');
    const cancelDeleteAccountBtn = document.getElementById('cancel-delete-account');
    const confirmDeleteAccountBtn = document.getElementById('confirm-delete-account');

    // Orchestrates the display transition for confirmation modals.
    const showModal = (modal) => {
        if (!modal) return;
        modal.classList.remove('hidden');
        void modal.offsetWidth;
        modal.classList.add('opacity-100');
        const modalDiv = modal.querySelector('div');
        if (modalDiv) {
            modalDiv.classList.remove('scale-95');
            modalDiv.classList.add('scale-100');
        }
    };

    // Orchestrates the hiding transition for confirmation modals with a delay for animations.
    const hideModal = (modal) => {
        if (!modal) return;
        modal.classList.remove('opacity-100');
        const modalDiv = modal.querySelector('div');
        if (modalDiv) {
            modalDiv.classList.remove('scale-100');
            modalDiv.classList.add('scale-95');
        }
        setTimeout(() => {
            modal.classList.add('hidden');
        }, 300);
    };

    // Centralizes event delegation for modal triggers across the application.
    document.addEventListener('click', (e) => {
        if (e.target.closest('.logout-trigger')) {
            e.preventDefault();
            showModal(logoutModal);
        }
        if (e.target.closest('.remove-pic-trigger')) {
            e.preventDefault();
            showModal(removePicModal);
        }
        if (e.target.closest('.delete-account-trigger')) {
            e.preventDefault();
            showModal(deleteAccountModal);
        }
        if (e.target === logoutModal) hideModal(logoutModal);
        if (e.target === removePicModal) hideModal(removePicModal);
        if (e.target === deleteAccountModal) hideModal(deleteAccountModal);
    });

    if (cancelBtn) cancelBtn.addEventListener('click', () => hideModal(logoutModal));
    if (cancelRemovePicBtn) cancelRemovePicBtn.addEventListener('click', () => hideModal(removePicModal));
    if (cancelDeleteAccountBtn) cancelDeleteAccountBtn.addEventListener('click', () => hideModal(deleteAccountModal));

    if (confirmRemovePicBtn) {
        confirmRemovePicBtn.addEventListener('click', () => {
            const form = document.getElementById('remove-pic-form');
            if (form) form.submit();
        });
    }

    if (confirmDeleteAccountBtn) {
        confirmDeleteAccountBtn.addEventListener('click', () => {
            const form = document.getElementById('delete-account-form');
            if (form) form.submit();
        });
    }

    // Disables browser native autocomplete for all user input fields to maintain security.
    document.querySelectorAll('input, textarea').forEach(el => {
        el.setAttribute('autocomplete', 'off');
    });

    // Facilitates on-demand field unlocking for user profile editing.
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

    // Injects a secure password visibility toggle into all designated password fields.
    document.querySelectorAll('input[type="password"]').forEach(input => {
        if (input.parentElement.classList.contains('pw-wrapper')) return;

        const wrapper = document.createElement('div');
        wrapper.className = 'pw-wrapper';
        wrapper.style.cssText = 'position:relative; display:flex; align-items:center;';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);

        input.style.flex = '1';
        input.style.minWidth = '0';
        input.style.paddingRight = '2.5rem';

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.style.cssText = 'position:absolute; right:0.75rem; top:50%; transform:translateY(-50%); display:flex; align-items:center; justify-content:center; background:none; border:none; cursor:pointer; padding:0; color:#94a3b8;';
        btn.innerHTML = '<span class="material-symbols-outlined" style="font-size:20px;line-height:1;">visibility</span>';
        wrapper.appendChild(btn);

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

    // Provides real-time feedback on password complexity requirements during entry.
    const pwCheckTargets = ['new_password', 'password'];
    const rules = [
        { label: 'At least 8 characters', test: v => v.length >= 8 },
        { label: 'One uppercase letter (A–Z)', test: v => /[A-Z]/.test(v) },
        { label: 'One number (0–9)', test: v => /\d/.test(v) },
        { label: 'One special character (!@#$%…)', test: v => /[!@#$%^&*()\-_=+\[\]{};':"\\|,.<>/?]/.test(v) },
    ];

    document.querySelectorAll('input[type="password"]').forEach(input => {
        if (!pwCheckTargets.includes(input.name)) return;

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
