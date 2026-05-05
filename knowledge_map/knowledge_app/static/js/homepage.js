console.log('homepage.js loaded');

document.addEventListener('DOMContentLoaded', function() {
    // @ts-nocheck

    // Read Django variables from data attributes
    const mapData = document.getElementById('map-data');
    const csrfToken = mapData.dataset.csrf;
    const mapId = mapData.dataset.mapId;
    const cyNodes = JSON.parse(mapData.dataset.nodes);
    const cyEdges = JSON.parse(mapData.dataset.edges);

    const addNodeUrl = `/custom-map/${mapId}/add-node/`;
    const addEdgeUrl = `/custom-map/${mapId}/add-edge/`;
    const updateTitleUrl = `/custom-map/${mapId}/update-title/`;

    // Initialise Cytoscape
    const cy = cytoscape({
        container: document.getElementById('cy'),
        elements: [...cyNodes, ...cyEdges],
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': '#0e223e',
                    'label': 'data(label)',
                    'color': '#fff',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'font-size': '12px',
                    'width': '120px',
                    'height': '40px',
                    'shape': 'roundrectangle',
                    'text-wrap': 'wrap',
                    'text-max-width': '110px',
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#9db8dd',
                    'target-arrow-color': '#9db8dd',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'label': 'data(label)',
                    'font-size': '10px',
                    'color': '#333',
                }
            },
            {
                selector: 'node.selected-source',
                style: {
                    'background-color': '#3b7ddd',
                    'border-width': '3px',
                    'border-color': '#fff',
                }
            }
        ],
        layout: { name: 'preset' }
    });

    // Cache DOM elements
    const popup = document.getElementById('node-popup');
    const popupLabel = document.getElementById('popup-label');
    const popupSummary = document.getElementById('popup-summary');
    const popupClose = document.getElementById('popup-close');
    const deleteNodeBtn = document.getElementById('delete-node-btn');
    const edgePopup = document.getElementById('edge-popup');
    const edgePopupLabel = document.getElementById('edge-popup-label');
    const edgePopupClose = document.getElementById('edge-popup-close');
    const deleteEdgeBtn = document.getElementById('delete-edge-btn');
    const addNodeBtn = document.getElementById('add-node-btn');
    const addEdgeBtn = document.getElementById('add-edge-btn');
    const addNodeForm = document.getElementById('add-node-form');
    const confirmAddNode = document.getElementById('confirm-add-node');
    const cancelAddNode = document.getElementById('cancel-add-node');
    const clearBtn = document.getElementById('clear-btn');
    const mapTitleInput = document.getElementById('map-title');

    let selectedNodeId = null;
    let selectedEdgeId = null;
    let edgeMode = false;
    let sourceNode = null;

    // ── Title update ──────────────────────────────────────────────────────────────
    mapTitleInput.addEventListener('blur', async function() {
        const title = mapTitleInput.value.trim();
        if (!title) return;
        await fetch(updateTitleUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ title })
        });
    });

    // ── Add node ──────────────────────────────────────────────────────────────────
    addNodeBtn.addEventListener('click', function() {
        addNodeForm.classList.remove('hidden');
        document.getElementById('new-node-label').focus();
    });

    cancelAddNode.addEventListener('click', function() {
        addNodeForm.classList.add('hidden');
        document.getElementById('new-node-label').value = '';
        document.getElementById('new-node-summary').value = '';
    });

    confirmAddNode.addEventListener('click', async function() {
        const label = document.getElementById('new-node-label').value.trim();
        const summary = document.getElementById('new-node-summary').value.trim();

        if (!label) {
            alert('Please enter a label for the node.');
            return;
        }

        const x = cy.width() / 2 + (Math.random() - 0.5) * 100;
        const y = cy.height() / 2 + (Math.random() - 0.5) * 100;

        try {
            const response = await fetch(addNodeUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ label, summary, x, y })
            });
            const data = await response.json();

            if (response.ok) {
                cy.add({
                    group: 'nodes',
                    data: { id: data.id, label: data.label, summary: data.summary },
                    position: { x, y }
                });
                addNodeForm.classList.add('hidden');
                document.getElementById('new-node-label').value = '';
                document.getElementById('new-node-summary').value = '';
            } else {
                alert(data.error || 'Failed to add node.');
            }
        } catch {
            alert('Network error. Failed to add node.');
        }
    });

    // ── Add connection (edge mode) ────────────────────────────────────────────────
    addEdgeBtn.addEventListener('click', function() {
        edgeMode = !edgeMode;
        sourceNode = null;

        if (edgeMode) {
            addEdgeBtn.textContent = 'Cancel Connection';
            addEdgeBtn.style.backgroundColor = '#856404';
            cy.nodes().style('border-width', '2px');
            cy.nodes().style('border-color', '#9db8dd');
        } else {
            resetEdgeMode();
        }
    });

    function resetEdgeMode() {
        if (sourceNode) sourceNode.removeClass('selected-source');
        sourceNode = null;
        edgeMode = false;
        addEdgeBtn.textContent = '+ Add Connection';
        addEdgeBtn.style.backgroundColor = '';
        cy.nodes().style('border-width', '0px');
    }

    // ── Node tap handler ──────────────────────────────────────────────────────────
    cy.on('tap', 'node', function(event) {
        const node = event.target;

        if (edgeMode) {
            if (!sourceNode) {
                sourceNode = node;
                node.addClass('selected-source');
            } else if (sourceNode.id() !== node.id()) {
                const label = prompt('Enter connection label (optional):') || '';

                fetch(addEdgeUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                    body: JSON.stringify({
                        source_id: sourceNode.data('id'),
                        target_id: node.data('id'),
                        label
                    })
                })
                .then(r => r.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                    } else {
                        cy.add({
                            group: 'edges',
                            data: { id: data.id, source: data.source, target: data.target, label: data.label }
                        });
                    }
                })
                .catch(() => alert('Failed to create connection.'))
                .finally(() => resetEdgeMode());
            }
            return;
        }

        // Normal mode - show popup
        selectedNodeId = node.data('id');
        popupLabel.textContent = node.data('label') || '';
        popupSummary.textContent = node.data('summary') || '';
        popup.classList.remove('hidden');
        edgePopup.classList.add('hidden');
    });

    // ── Edge tap handler ──────────────────────────────────────────────────────────
    cy.on('tap', 'edge', function(event) {
        if (edgeMode) return;
        const edge = event.target;
        selectedEdgeId = edge.data('id').replace('e', '');
        edgePopupLabel.textContent = edge.data('label') || '';
        edgePopup.classList.remove('hidden');
        popup.classList.add('hidden');
    });

    // Close popups when clicking background
    cy.on('tap', function(event) {
        if (event.target === cy) {
            popup.classList.add('hidden');
            edgePopup.classList.add('hidden');
            selectedNodeId = null;
            selectedEdgeId = null;
        }
    });

    // ── Save node position after drag ─────────────────────────────────────────────
    cy.on('dragfree', 'node', async function(event) {
        const node = event.target;
        const pos = node.position();
        const nodeId = node.data('id');
        const updateUrl = `/custom-map/${mapId}/update-node/${nodeId}/`;

        await fetch(updateUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ x: pos.x, y: pos.y })
        });
    });

    // ── Close popups ──────────────────────────────────────────────────────────────
    popupClose.addEventListener('click', function() {
        popup.classList.add('hidden');
        selectedNodeId = null;
    });

    edgePopupClose.addEventListener('click', function() {
        edgePopup.classList.add('hidden');
        selectedEdgeId = null;
    });

    // ── Delete node ───────────────────────────────────────────────────────────────
    deleteNodeBtn.addEventListener('click', async function() {
        if (!selectedNodeId) return;
        if (!confirm('Delete this node?')) return;

        const deleteUrl = `/custom-map/${mapId}/delete-node/${selectedNodeId}/`;

        try {
            const response = await fetch(deleteUrl, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken }
            });

            if (response.ok) {
                cy.getElementById(selectedNodeId).remove();
                popup.classList.add('hidden');
                selectedNodeId = null;
            } else {
                alert('Failed to delete node.');
            }
        } catch {
            alert('Network error. Failed to delete node.');
        }
    });

    // ── Delete edge ───────────────────────────────────────────────────────────────
    deleteEdgeBtn.addEventListener('click', async function() {
        if (!selectedEdgeId) return;
        if (!confirm('Delete this connection?')) return;

        const deleteUrl = `/custom-map/${mapId}/delete-edge/${selectedEdgeId}/`;

        try {
            const response = await fetch(deleteUrl, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken }
            });

            if (response.ok) {
                cy.getElementById(`e${selectedEdgeId}`).remove();
                edgePopup.classList.add('hidden');
                selectedEdgeId = null;
            } else {
                alert('Failed to delete connection.');
            }
        } catch {
            alert('Network error. Failed to delete connection.');
        }
    });

    // ── Clear all ─────────────────────────────────────────────────────────────────
    clearBtn.addEventListener('click', async function() {
        if (!confirm('Are you sure you want to clear the entire map?')) return;

        const nodes = cy.nodes().map(n => n.data('id'));
        for (const nodeId of nodes) {
            await fetch(`/custom-map/${mapId}/delete-node/${nodeId}/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken }
            });
        }
        cy.elements().remove();
        popup.classList.add('hidden');
        edgePopup.classList.add('hidden');
    });
});