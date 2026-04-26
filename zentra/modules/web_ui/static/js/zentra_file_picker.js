/**
 * ZENTRA FILE PICKER — Standalone Utility Module
 * Purpose: Service-safe system path selection.
 * Distinction: Minimalist UI, specialized for config tasks.
 */

window.ZentraFilePicker = {
    _modal: null,
    _onSelect: null,
    _currentPath: null,
    _selectedPath: null,
    _options: {
        title: "Select File or Folder",
        hideSelect: false, // if true, only browse/view
        mode: 'any'        // 'any', 'file', 'dir'
    },

    open(options = {}) {
        this._options = { ...this._options, ...options };
        this._onSelect = options.onSelect || null;
        this._selectedPath = null;
        this._renderModal();
        this._loadDrives();
        
        const startPath = options.initialPath || 'C:\\';
        this._browse(startPath);
    },

    close() {
        if (this._modal) {
            this._modal.remove();
            this._modal = null;
        }
    },

    async _loadDrives() {
        try {
            const r = await fetch('/api/system/explorer/drives');
            const d = await r.json();
            if (!d.ok) return;
            const container = this._modal.querySelector('.zentra-picker-drives');
            container.innerHTML = d.drives.map(drv => 
                `<span class="zp-drive-tag" onclick="ZentraFilePicker._browse('${drv.replace(/\\/g, '\\\\')}')">💾 ${drv}</span>`
            ).join('');
        } catch (e) { console.error(e); }
    },

    async _browse(path) {
        try {
            const body = this._modal.querySelector('.zentra-picker-body');
            body.innerHTML = '<div style="padding:20px; color:var(--muted); font-size:12px;">Scanning...</div>';

            const r = await fetch('/api/system/explorer/ls', {
                method: 'POST', body: JSON.stringify({ path })
            });
            const d = await r.json();
            if (!d.ok) {
                body.innerHTML = `<div style="padding:20px; color:var(--red); font-size:12px;">Error: ${d.error}</div>`;
                return;
            }

            this._currentPath = d.current;
            this._modal.querySelector('.zentra-picker-path-box').textContent = d.current;

            let html = '';
            if (d.parent) {
                html += `<div class="zentra-picker-item" onclick="ZentraFilePicker._browse('${d.parent.replace(/\\/g, '\\\\')}')">
                    <span class="zentra-picker-icon">⬅️</span>
                    <span class="zentra-picker-name">.. (Parent Directory)</span>
                </div>`;
            }

            d.entries.forEach(e => {
                const icon = e.type === 'dir' ? '📁' : '📄';
                const safePath = e.path.replace(/\\/g, '\\\\');
                html += `<div class="zentra-picker-item" 
                             onclick="ZentraFilePicker._selectItem('${safePath}', ${e.type === 'dir'})"
                             ondblclick="${e.type === 'dir' ? `ZentraFilePicker._browse('${safePath}')` : 'ZentraFilePicker._confirm()'}">
                    <span class="zentra-picker-icon">${icon}</span>
                    <span class="zentra-picker-name">${e.name}</span>
                </div>`;
            });

            body.innerHTML = html;
            this._modal.querySelector('#zp-confirm-btn').disabled = true;
        } catch (e) { console.error(e); }
    },

    _selectItem(path, isDir) {
        this._selectedPath = path;
        this._modal.querySelectorAll('.zentra-picker-item').forEach(el => el.classList.remove('selected'));
        // Find the element and select it
        event.currentTarget.classList.add('selected');

        const btn = this._modal.querySelector('#zp-confirm-btn');
        btn.disabled = false;
        
        // If we are in browse-only mode, we don't care about the confirm button being enabled
        if (this._options.hideSelect) btn.disabled = true;
    },

    _confirm() {
        if (this._onSelect && this._selectedPath) {
            this._onSelect(this._selectedPath);
        }
        this.close();
    },

    _renderModal() {
        const modal = document.createElement('div');
        modal.className = 'zentra-picker-modal';
        modal.innerHTML = `
            <div class="zentra-picker-content">
                <div class="zentra-picker-header">
                    <h3 class="zentra-picker-title">📦 ${this._options.title}</h3>
                    <button class="zentra-picker-close" onclick="ZentraFilePicker.close()">×</button>
                </div>
                <div class="zentra-picker-nav">
                    <div class="zentra-picker-path-box">Initializing...</div>
                </div>
                <div class="zentra-picker-drives"></div>
                <div class="zentra-picker-body"></div>
                <div class="zentra-picker-footer">
                    <button class="zp-btn zp-btn-secondary" onclick="ZentraFilePicker.close()">Cancel</button>
                    ${this._options.hideSelect ? '' : '<button class="zp-btn zp-btn-primary" id="zp-confirm-btn" onclick="ZentraFilePicker._confirm()" disabled>Select Path</button>'}
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        this._modal = modal;
        
        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.close();
        });
    }
};
