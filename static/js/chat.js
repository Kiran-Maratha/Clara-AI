document.addEventListener('DOMContentLoaded', () => {
    // Configure marked for better link support and formatting
    marked.setOptions({
        gfm: true,
        breaks: true,
        headerIds: false,
        mangle: false
    });

    // Auto-expanding textarea logic
    const messageInput = document.getElementById('message-input');
    if (messageInput) {
        messageInput.addEventListener('input', function () {
            this.style.height = 'auto'; // Reset height to recalculate
            this.style.height = (this.scrollHeight) + 'px'; // Set new height based on content
        });
        // Handle Shift+Enter for new lines, Enter to submit
        messageInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (this.value.trim() !== '') {
                    document.getElementById('chat-form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
                }
            }
        });
    }
    // Suggestion Card Select logic
    const cards = document.querySelectorAll('.suggestion-card');
    const contextInput = document.getElementById('issue-context');

    cards.forEach(card => {
        card.addEventListener('click', () => {
            const isSelected = card.classList.contains('ring-2');

            // Clear all cards first
            cards.forEach(c => c.classList.remove('ring-2', 'ring-blue-500', 'bg-white', 'dark:ring-blue-500', 'dark:bg-[#111822]'));
            contextInput.value = '';

            if (!isSelected) {
                // Select this card if it wasn't already selected
                card.classList.add('ring-2', 'ring-blue-500', 'bg-white', 'dark:ring-blue-500', 'dark:bg-[#111822]');
                contextInput.value = card.dataset.context;
            }
        });
    });

    // Mobile Sidebar Logic
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const closeSidebarBtn = document.getElementById('close-sidebar-btn');
    const sidebar = document.getElementById('sidebar');
    const mobileOverlay = document.getElementById('mobile-overlay');

    const toggleSidebar = () => {
        sidebar.classList.toggle('-translate-x-full');
        mobileOverlay.classList.toggle('hidden');
    };

    if (mobileMenuBtn && sidebar && mobileOverlay) {
        mobileMenuBtn.addEventListener('click', toggleSidebar);
        mobileOverlay.addEventListener('click', toggleSidebar);
        if (closeSidebarBtn) closeSidebarBtn.addEventListener('click', toggleSidebar);
    }

    // Star toggle
    document.body.addEventListener('click', async (e) => {
        const btn = e.target.closest('.star-btn');
        if (!btn) return;

        e.stopPropagation();
        const chatId = btn.dataset.chatId;
        const res = await fetch(`/api/chat/${chatId}/star`, { method: 'POST' });
        const data = await res.json();
        const icon = btn.querySelector('span');

        if (data.starred) {
            icon.style.fontVariationSettings = "'FILL' 1";
            btn.classList.add('text-blue-500');
            btn.classList.remove('text-slate-400');
        } else {
            icon.style.fontVariationSettings = "'FILL' 0";
            btn.classList.remove('text-blue-500');
            btn.classList.add('text-slate-400');
        }
    });

    // Delete Chat logic
    let chatToDelete = null;
    const deleteModal = document.getElementById('delete-chat-modal');
    const confirmDeleteBtn = document.getElementById('confirm-delete-chat');
    const cancelDeleteBtn = document.getElementById('cancel-delete-chat');

    document.body.addEventListener('click', (e) => {
        const btn = e.target.closest('.delete-chat-btn');
        if (!btn) return;

        e.stopPropagation();
        chatToDelete = btn.dataset.chatId;

        if (deleteModal) {
            deleteModal.classList.remove('hidden');
            setTimeout(() => {
                deleteModal.classList.remove('opacity-0');
                deleteModal.querySelector('div').classList.remove('scale-95');
            }, 10);
        }
    });

    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', () => {
            if (deleteModal) {
                deleteModal.classList.add('opacity-0');
                deleteModal.querySelector('div').classList.add('scale-95');
                setTimeout(() => deleteModal.classList.add('hidden'), 300);
            }
            chatToDelete = null;
        });
    }

    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', async () => {
            if (!chatToDelete) return;

            try {
                const res = await fetch(`/api/chat/${chatToDelete}`, { method: 'DELETE' });
                const data = await res.json();

                if (data.success) {
                    const item = document.querySelector(`.chat-item[data-chat-id="${chatToDelete}"]`);
                    if (item) item.remove();

                    // If we deleted the current chat or no chats left, redirect to new chat
                    if (chatToDelete == currentChatId || document.querySelectorAll('.chat-item').length === 0) {
                        window.location.href = '/';
                    }
                }
            } catch (err) {
                console.error("Deletion error:", err);
            } finally {
                cancelDeleteBtn.click(); // Hide modal
            }
        });
    }

    // Chat history load
    let currentChatId = null;

    function highlightChatItem(chatId) {
        document.querySelectorAll('.chat-item').forEach(item => {
            const isActive = item.dataset.chatId == chatId;
            item.classList.toggle('bg-blue-50', isActive);
            item.classList.toggle('dark:bg-blue-500/10', isActive);
            item.classList.toggle('border', isActive);
            item.classList.toggle('border-blue-200', isActive);
            item.classList.toggle('dark:border-blue-500/30', isActive);
            item.classList.toggle('text-brand-dark', isActive);
            item.classList.toggle('dark:text-white', isActive);
            if (!isActive) {
                item.classList.remove('text-brand-dark', 'dark:text-white');
                item.classList.add('text-slate-600', 'dark:text-slate-400');
            } else {
                item.classList.remove('text-slate-600', 'dark:text-slate-400');
            }
        });
    }

    function updateChatSidebar(chatId, title) {
        let item = document.querySelector(`.chat-item[data-chat-id="${chatId}"]`);
        if (item) {
            // Update existing item title
            const btn = item.querySelector('.chat-load-btn');
            if (btn) btn.textContent = title;
        } else {
            // Add new item to top of list
            const nav = document.getElementById('chat-nav');
            if (!nav) return;

            const newItemHtml = `
                <div class="chat-item group flex items-center rounded-lg transition text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                    data-chat-id="${chatId}">
                    <button class="chat-load-btn flex-1 text-left px-3 py-2.5 text-sm font-medium truncate" data-chat-id="${chatId}">
                        ${title}
                    </button>
                    <div class="flex items-center space-x-0.5 opacity-0 group-hover:opacity-100 transition pr-1">
                        <button class="star-btn flex items-center justify-center p-1.5 rounded-md hover:bg-slate-100 dark:hover:bg-slate-700 transition text-slate-400 hover:text-blue-400"
                            data-chat-id="${chatId}" data-starred="false">
                            <span class="material-symbols-outlined text-[18px]" style="font-variation-settings: 'FILL' 0">grade</span>
                        </button>
                        <button class="delete-chat-btn flex items-center justify-center p-1.5 rounded-md hover:bg-red-50 dark:hover:bg-red-900/20 text-slate-400 hover:text-red-500 transition"
                            data-chat-id="${chatId}">
                            <span class="material-symbols-outlined text-[18px]">delete</span>
                        </button>
                    </div>
                </div>
            `;
            nav.insertAdjacentHTML('afterbegin', newItemHtml);

            // Re-attach load event to NEW button
            const newBtn = nav.querySelector(`.chat-item[data-chat-id="${chatId}"] .chat-load-btn`);
            if (newBtn) {
                newBtn.addEventListener('click', async () => {
                    currentChatId = chatId;
                    highlightChatItem(chatId);
                    const res = await fetch(`/api/chat/${chatId}/messages`);
                    const data = await res.json();
                    if (data.messages) renderMessages(data.messages);
                });
            }
        }
        highlightChatItem(chatId);
    }

    function renderMessages(messages) {
        const chatHistory = document.getElementById('chat-history');
        const heroText = document.getElementById('hero-text');
        const suggestionCards = document.querySelector('.grid');

        chatHistory.innerHTML = '';
        if (heroText) heroText.style.display = 'none';
        if (suggestionCards) suggestionCards.style.display = 'none';

        messages.forEach(msg => {
            if (msg.sender === 'user') {
                chatHistory.insertAdjacentHTML('beforeend', `
                    <div class="flex justify-end mb-4">
                        <div class="bg-brand-dark dark:bg-blue-600 text-white px-4 py-2.5 rounded-2xl rounded-tr-sm text-sm max-w-[85%] lg:max-w-[75%] shadow-sm">${msg.content.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>
                    </div>`);
            } else {
                const aiBubble = `
                    <div class="flex justify-start mb-6">
                        <div class="bg-white dark:bg-[#161b22] dark:text-slate-200 border border-slate-200 dark:border-[#1d232c] p-4 md:p-5 rounded-2xl rounded-tl-sm max-w-[90%] md:max-w-[85%] shadow-sm">
                            <div class="flex items-center space-x-2 mb-3">
                                <div class="w-6 h-6 rounded bg-brand-dark dark:bg-blue-500 flex items-center justify-center text-white shrink-0">
                                    <span class="material-symbols-outlined text-[14px]">bolt</span>
                                </div>
                                <div class="font-bold text-xs text-brand-dark dark:text-blue-400">Clara AI</div>
                            </div>
                            <div class="ai-bubble-content text-sm md:text-[15px] leading-relaxed">${marked.parse(msg.content)}</div>
                        </div>
                    </div>
                `;
                chatHistory.insertAdjacentHTML('beforeend', aiBubble);
            }
        });
        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
        const chatScroll = document.getElementById('chat-scroll');
        if (chatScroll) chatScroll.scrollTop = chatScroll.scrollHeight;
    }

    document.querySelectorAll('.chat-load-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const chatId = btn.dataset.chatId;
            currentChatId = chatId;
            highlightChatItem(chatId);
            const res = await fetch(`/api/chat/${chatId}/messages`);
            const data = await res.json();
            if (data.messages) renderMessages(data.messages);
        });
    });

    // File Attachment Logic
    const fileInput = document.getElementById('chat-file-input');
    const attachBtn = document.getElementById('attach-btn');
    const videoBtn = document.getElementById('video-btn');
    const previewContainer = document.getElementById('file-preview-container');
    const previewList = document.getElementById('file-preview-list');

    let selectedFiles = [];

    if (attachBtn) {
        attachBtn.addEventListener('click', () => { fileInput.setAttribute('accept', 'image/*,.pdf,.txt,.csv'); fileInput.click(); });
    }
    if (videoBtn) {
        videoBtn.addEventListener('click', () => { fileInput.setAttribute('accept', 'video/*'); fileInput.click(); });
    }

    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const newFiles = Array.from(e.target.files);
            selectedFiles = [...selectedFiles, ...newFiles];
            renderPreviews();
            // Reset input so same file can be selected again if removed
            fileInput.value = '';
        });
    }

    function renderPreviews() {
        if (!previewList) return;
        previewList.innerHTML = '';
        if (selectedFiles.length > 0) {
            previewContainer.classList.remove('hidden');
            selectedFiles.forEach((file, index) => {
                let displayIcon = 'description';
                if (file.type.startsWith('image/')) displayIcon = 'image';
                else if (file.type.startsWith('video/')) displayIcon = 'videocam';

                const el = document.createElement('div');
                el.className = 'flex items-center space-x-2 bg-white dark:bg-[#1d232c] border border-slate-200 dark:border-slate-700 px-3 py-1.5 rounded-lg shadow-sm';
                el.innerHTML = `
                    <span class="material-symbols-outlined text-slate-400 text-[16px]">${displayIcon}</span>
                    <span class="text-xs font-medium text-slate-700 dark:text-slate-300 truncate max-w-[120px]">${file.name}</span>
                    <button type="button" class="remove-file text-slate-400 hover:text-red-500 transition ml-1" data-id="${index}">
                        <span class="material-symbols-outlined text-[16px]">close</span>
                    </button>
                `;
                previewList.appendChild(el);
            });

            document.querySelectorAll('.remove-file').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const idx = parseInt(e.currentTarget.dataset.id);
                    selectedFiles.splice(idx, 1);
                    renderPreviews();
                });
            });
        } else {
            previewContainer.classList.add('hidden');
        }
    }

    // AJAX Chat handling with FormData
    const chatForm = document.getElementById('chat-form');
    const chatHistory = document.getElementById('chat-history');
    const heroText = document.getElementById('hero-text');
    const suggestionCards = document.querySelector('.grid');

    if (chatForm && chatForm.getAttribute('method') === 'POST') {
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const input = chatForm.querySelector('textarea[name="message"]');
            const chatScroll = document.getElementById('chat-scroll');
            const message = input.value.trim();
            const context = document.getElementById('issue-context').value;

            if (!message && selectedFiles.length === 0) return;

            // Hide hero & suggestions for a cleaner chat view
            if (heroText) heroText.style.display = 'none';
            if (suggestionCards) suggestionCards.style.display = 'none';

            // Show user message
            let attachmentPills = '';
            if (selectedFiles.length > 0) {
                attachmentPills = `<div class="flex flex-wrap gap-1 mb-2 justify-end">` + selectedFiles.map(f => `<span class="bg-blue-500/20 text-blue-100 text-[10px] px-2 py-0.5 rounded border border-blue-400/30 flex items-center"><span class="material-symbols-outlined text-[12px] mr-1">attach_file</span>${f.name}</span>`).join('') + `</div>`;
            }

            const userBubble = `
                <div class="flex justify-end mb-4">
                    <div class="bg-brand-dark dark:bg-blue-600 text-white px-4 py-2.5 rounded-2xl rounded-tr-sm text-sm max-w-[85%] lg:max-w-[75%] shadow-sm">
                        ${attachmentPills}
                        ${message ? message.replace(/</g, "&lt;").replace(/>/g, "&gt;") : ''}
                    </div>
                </div>
            `;
            chatHistory.insertAdjacentHTML('beforeend', userBubble);

            input.value = '';
            input.style.height = 'auto'; // Reset height
            const filesToSend = [...selectedFiles];
            selectedFiles = [];
            renderPreviews();

            // Show thinking indicator
            const thinkingId = 'thinking-' + Date.now();
            const thinkingBubble = `
                <div id="${thinkingId}" class="flex justify-start mb-6">
                    <div class="bg-white dark:bg-[#161b22] border border-slate-200 dark:border-[#1d232c] p-4 rounded-2xl rounded-tl-sm shadow-sm flex items-center space-x-3">
                        <div class="w-6 h-6 rounded bg-brand-dark dark:bg-blue-500 flex items-center justify-center text-white shrink-0 animate-spin-slow">
                            <span class="material-symbols-outlined text-[14px]">bolt</span>
                        </div>
                        <div class="flex space-x-1">
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                        </div>
                    </div>
                </div>
            `;
            chatHistory.insertAdjacentHTML('beforeend', thinkingBubble);
            if (chatScroll) chatScroll.scrollTop = chatScroll.scrollHeight;

            // Send button state
            const btnIcon = chatForm.querySelector('button[type="submit"] span');
            const prevIcon = btnIcon ? btnIcon.textContent : 'send';
            if (btnIcon) {
                btnIcon.textContent = 'pending';
                btnIcon.classList.add('animate-pulse');
            }

            try {
                const formData = new FormData();
                formData.append('message', message);
                formData.append('issue_context', context);
                if (currentChatId) formData.append('chat_id', currentChatId);

                filesToSend.forEach(file => {
                    formData.append('attachments', file);
                });

                const res = await fetch('/api/chat', {
                    method: 'POST',
                    body: formData
                });

                const data = await res.json();

                // Remove thinking indicator
                const loader = document.getElementById(thinkingId);
                if (loader) loader.remove();

                if (data.error) {
                    const err = data.error.includes("offline") ? data.error : "sorry ai currently offline, please check in later....";
                    const errorBubble = `
                        <div class="flex justify-start mb-4">
                            <div class="flex items-center space-x-3 text-slate-500 dark:text-slate-400 text-[11px] font-medium p-4 border border-slate-200 dark:border-slate-800/50 bg-slate-50/50 dark:bg-slate-900/30 rounded-2xl w-full max-w-[85%]">
                                <span class="material-symbols-outlined text-[18px] opacity-60">sentiment_dissatisfied</span>
                                <span class="uppercase tracking-wider">${err}</span>
                            </div>
                        </div>`;
                    chatHistory.insertAdjacentHTML('beforeend', errorBubble);
                } else if (!data.response) {
                    const errorBubble = `
                        <div class="flex justify-start mb-4">
                            <div class="flex items-center space-x-3 text-slate-500 dark:text-slate-400 text-[11px] font-medium p-4 border border-slate-200 dark:border-slate-800/50 bg-slate-50/50 dark:bg-slate-900/30 rounded-2xl w-full max-w-[85%]">
                                <span class="material-symbols-outlined text-[18px] opacity-60">sentiment_dissatisfied</span>
                                <span class="uppercase tracking-wider">sorry ai currently offline, please check in later....</span>
                            </div>
                        </div>`;
                    chatHistory.insertAdjacentHTML('beforeend', errorBubble);
                } else {
                    const aiBubble = `
                        <div class="flex justify-start mb-6">
                            <div class="bg-white dark:bg-[#161b22] dark:text-slate-200 border border-slate-200 dark:border-[#1d232c] p-4 md:p-5 rounded-2xl rounded-tl-sm max-w-[90%] md:max-w-[85%] shadow-sm">
                                <div class="flex items-center space-x-2 mb-3">
                                    <div class="w-6 h-6 rounded bg-brand-dark dark:bg-blue-500 flex items-center justify-center text-white shrink-0">
                                        <span class="material-symbols-outlined text-[14px]">bolt</span>
                                    </div>
                                    <div class="font-bold text-xs text-brand-dark dark:text-blue-400">Clara AI</div>
                                </div>
                                <div class="ai-bubble-content text-sm md:text-[15px] leading-relaxed">${marked.parse(data.response)}</div>
                            </div>
                        </div>
                    `;
                    chatHistory.insertAdjacentHTML('beforeend', aiBubble);

                    // Update Sidebar Dynamic logic
                    if (data.chat_id) {
                        currentChatId = data.chat_id;
                        if (data.title) {
                            updateChatSidebar(data.chat_id, data.title);
                        }
                    }

                    document.querySelectorAll('pre code').forEach((block) => {
                        hljs.highlightElement(block);
                    });
                }
            } catch (err) {
                console.error("Chat error:", err);
                const loader = document.getElementById(thinkingId);
                if (loader) loader.remove();
                const errorBubble = `
                    <div class="flex justify-start mb-4">
                        <div class="flex items-center space-x-3 text-slate-500 dark:text-slate-400 text-[11px] font-medium p-4 border border-slate-200 dark:border-slate-800/50 bg-slate-50/50 dark:bg-slate-900/30 rounded-2xl w-full max-w-[85%]">
                            <span class="material-symbols-outlined text-[18px] opacity-60">cloud_off</span>
                            <span class="uppercase tracking-wider">sorry ai currently offline, please check in later....</span>
                        </div>
                    </div>`;
                chatHistory.insertAdjacentHTML('beforeend', errorBubble);
            } finally {
                if (btnIcon) {
                    btnIcon.textContent = prevIcon;
                    btnIcon.classList.remove('animate-pulse');
                }
                if (chatScroll) chatScroll.scrollTop = chatScroll.scrollHeight;
            }
        });
    }

    // Hacker scramble effect for hero tagline
    const tagline = document.getElementById('tagline');
    if (tagline) {
        const originalText = tagline.innerText;
        const chars = "ABCDEFGHIJKLMOPQRSTUVWXYZ0123456789@#$%&*";
        let interval = null;

        const scramble = () => {
            clearInterval(interval);
            const durations = originalText.split("").map((char) => char === " " ? 0 : Math.floor(Math.random() * 15) + 10);
            let frame = 0;

            interval = setInterval(() => {
                let finished = true;
                tagline.innerText = originalText
                    .split("")
                    .map((letter, index) => {
                        if (frame >= durations[index]) return originalText[index];
                        if (letter === " ") return " ";
                        finished = false;
                        return chars[Math.floor(Math.random() * chars.length)];
                    })
                    .join("");

                if (finished) {
                    clearInterval(interval);
                    tagline.innerText = originalText;
                }
                frame++;
            }, 50);
        };

        // Delay slightly for dramatic effect
        setTimeout(scramble, 400);
        tagline.addEventListener('mouseenter', scramble);
    }
});
