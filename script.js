const updaters = [
    'github-updater',
    'instagram-updater',
    'leetcode-updater',
    'linkedin-updater',
    'youtube-updater'
];

async function fetchStats() {
    const dashboard = document.getElementById('dynamic-stats');
    dashboard.innerHTML = ''; // Clear loading state

    let platformResults = [];

    for (const updater of updaters) {
        const platformName = updater.replace('-updater', '');
        try {
            const response = await fetch(`./${updater}/output.json`);
            
            if (!response.ok) {
                console.warn(`Could not fetch data for ${updater}`);
                platformResults.push({ platformName, data: null, isError: true });
                continue;
            }

            const data = await response.json();
            
            if (data && data.length > 0) {
                platformResults.push({ platformName, data, isError: false });
            } else {
                platformResults.push({ platformName, data: null, isError: true });
            }
        } catch (error) {
            console.error(`Error loading data for ${updater}:`, error);
            platformResults.push({ platformName, data: null, isError: true });
        }
    }

    // Sort: active platforms first, error platforms last
    platformResults.sort((a, b) => (a.isError === b.isError) ? 0 : a.isError ? 1 : -1);

    platformResults.forEach(result => {
        if (result.isError) {
            renderEmptyPlatformSection(result.platformName, dashboard);
        } else {
            renderPlatformSection(result.platformName, result.data, dashboard);
        }
    });

    if (dashboard.innerHTML === '') {
        dashboard.innerHTML = '<div class="loading-state">No stats data found yet. Try running the updaters first!</div>';
    }
}

function renderEmptyPlatformSection(platform, container) {
    const section = document.createElement('div');
    section.className = 'platform-section';

    const header = document.createElement('div');
    header.className = 'platform-header';
    header.innerHTML = `<h2 class="platform-title">${platform} Stats</h2>`;
    
    const message = document.createElement('div');
    message.className = 'loading-state';
    message.style.padding = '2rem 0';
    message.textContent = 'Data not available (file not found or empty). Please run the updaters to generate stats.';

    section.appendChild(header);
    section.appendChild(message);
    container.appendChild(section);
}

function renderPlatformSection(platform, data, container) {
    const section = document.createElement('div');
    section.className = 'platform-section';

    const header = document.createElement('div');
    header.className = 'platform-header';
    header.innerHTML = `<h2 class="platform-title">${platform} Stats</h2>`;
    
    const grid = document.createElement('div');
    grid.className = 'cards-grid';

    data.forEach(user => {
        const card = createUserCard(user);
        grid.appendChild(card);
    });

    section.appendChild(header);
    section.appendChild(grid);
    container.appendChild(section);
}

function createUserCard(user) {
    const card = document.createElement('div');
    card.className = 'card';

    const isFailed = user.status === 'failed';
    const statusClass = isFailed ? 'status-failed' : 'status-success';
    const statusText = isFailed ? 'Failed' : 'Active';

    let html = `
        <div class="card-header">
            <div>
                <div class="user-name">${user.name || 'Unknown User'}</div>
                <div class="user-handle">${user.handle || user.username || 'unknown'}</div>
            </div>
            <span class="status-badge ${statusClass}">${statusText}</span>
        </div>
    `;

    if (!isFailed) {
        html += '<div class="stats-grid">';
        
        // Render all keys that aren't metadata
        const metadataKeys = ['id', 'name', 'handle', 'username', 'status', 'reason', 'last_updated'];
        
        const flatUser = flattenObject(user);
        
        Object.entries(flatUser).forEach(([key, value]) => {
            if (!metadataKeys.includes(key)) {
                // Format the label nicely
                const label = escapeHtml(key.replace(/_/g, ' '));
                const formattedValue = formatValue(value);
                const isLongText = (typeof value === 'string' && value.length > 50) || Array.isArray(value);
                
                if (formattedValue !== null && formattedValue !== '') {
                    html += `
                        <div class="stat-item ${isLongText ? 'full-width' : ''}">
                            <span class="stat-label">${label}</span>
                            <span class="stat-value">${formattedValue}</span>
                        </div>
                    `;
                }
            }
        });
        
        html += '</div>';
    } else {
        html += `
            <div class="error-message">
                <strong>Error:</strong> ${user.reason || 'Unknown error occurred'}
            </div>
        `;
    }

    const lastUpdated = user.last_updated 
        ? new Date(user.last_updated).toLocaleString() 
        : 'Unknown';

    html += `
        <div class="card-footer">
            <span>Last Updated</span>
            <span>${lastUpdated}</span>
        </div>
    `;

    card.innerHTML = html;
    return card;
}

// Initialize
document.addEventListener('DOMContentLoaded', fetchStats);

function flattenObject(object, parentKey = '') {
    const flattened = {};

    if (!object || typeof object !== 'object' || Array.isArray(object)) {
        return flattened;
    }

    Object.entries(object).forEach(([key, value]) => {
        const flattenedKey = parentKey ? parentKey + '_' + key : key;

        if (value && typeof value === 'object' && !Array.isArray(value)) {
            // Stat objects use the human-readable display value and keep the
            // underlying numeric value out of the dashboard.
            if (Object.prototype.hasOwnProperty.call(value, 'display') &&
                Object.prototype.hasOwnProperty.call(value, 'value')) {
                flattened[flattenedKey] = value.display;
            } else {
                Object.assign(flattened, flattenObject(value, flattenedKey));
            }
        } else {
            flattened[flattenedKey] = value;
        }
    });

    return flattened;
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function formatValue(value) {
    if (value === null || value === undefined) return 'N/A';

    if (Array.isArray(value)) {
        return value.map(item => formatValue(item)).join('<br>');
    }

    if (typeof value === 'string' && /^https?:\/\//i.test(value)) {
        const safeValue = escapeHtml(value);
        const isImage = /\.(png|jpe?g|gif)(?:[?#]|$)/i.test(value) ||
            /avatar|yt3/i.test(value);

        if (isImage) {
            return '<img src="' + safeValue + '" alt="Profile image" loading="lazy">';
        }

        return '<a href="' + safeValue + '" target="_blank" rel="noopener noreferrer">' + safeValue + '</a>';
    }

    if (typeof value === 'number') return value.toLocaleString();
    if (typeof value === 'object') return escapeHtml(JSON.stringify(value));
    return escapeHtml(value);
}
