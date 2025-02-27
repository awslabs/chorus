from flask import Flask, render_template_string, jsonify
import os
import threading
import webbrowser
from typing import Dict, Optional, List
import time
import logging
import json


VISUAL_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Chorus Visual Debugger</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <style>
        body { 
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: #f0f0f0;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #1a1a1a;
            color: white;
            padding: 15px 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .view-toggle {
            padding: 10px 20px;
            background: #2196F3;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        .view-toggle:hover {
            background: #1976D2;
        }
        .content {
            padding: 0 20px;
        }
        .side-by-side {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            max-width: 100%;
            margin: 0 auto;
            padding: 0 20px 20px 20px;
        }
        .tab-view {
            display: none;
        }
        .tab-buttons {
            display: none;
            margin-bottom: 20px;
        }
        .tab-btn {
            padding: 10px 20px;
            margin-right: 5px;
            background: #ddd;
            border: none;
            border-radius: 5px 5px 0 0;
            cursor: pointer;
        }
        .tab-btn.active {
            background: white;
        }
        .panel {
            background: white;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            min-width: 0;
            min-height: 600px;
            max-height: 600px;
            overflow-y: auto;
        }
        .tab-view .panel.global-messages {
            grid-column: 1 / -1;  /* Only span all columns in tab view */
            max-height: 300px;
        }
        .panel.tab {
            display: none;
        }
        .panel.tab.active {
            display: block;
        }
        .panel h2 {
            margin-top: 0;
            color: #333;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        .panel-content {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 50%;
            gap: 15px;
            height: calc(100% - 50px); /* Subtract header height */
        }
        .global-messages .panel-content {
            grid-template-columns: 1fr;  /* Full width for messages in Global Messages panel */
        }
        .panel.global-messages .messages {
            border-left: none;
            padding-left: 0;
            min-width: 0;
        }
        .output {
            min-width: 0;
            overflow-x: auto;
            overflow-y: auto;
            height: 100%;
        }
        .messages {
            border-left: 1px solid #eee;
            padding-left: 15px;
            min-width: 300px;
            overflow-y: auto;
            height: 100%;
        }
        .message {
            margin-bottom: 10px;
            padding: 8px;
            border-radius: 4px;
            font-size: 12px;
        }
        .message.sent {
            background: #e3f2fd;
            border-left: 3px solid #2196F3;
        }
        .message.received {
            background: #f5f5f5;
            border-left: 3px solid #9e9e9e;
        }
        .message-header {
            font-weight: bold;
            margin-bottom: 4px;
        }
        pre {
            background: #f8f8f8;
            padding: 10px;
            border-radius: 3px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            margin: 0;
        }
        .scrollable-content {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #eee;
            padding: 8px;
            margin-top: 4px;
        }
        .message-content {
            max-height: 200px;
            overflow-y: auto;
            margin-top: 4px;
        }
        .refresh-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 10px 20px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            z-index: 1000;
        }
        .refresh-btn:hover {
            background: #45a049;
        }
        .team-info {
            display: none;
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 80%;
            height: 80%;
            background: white;
            z-index: 1001;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.5);
            overflow-y: auto;
        }
        .team-section {
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #2196F3;
        }
        .agent-section {
            margin: 10px 0;
            padding: 15px;
            background: white;
            border-radius: 5px;
            border: 1px solid #e0e0e0;
        }
        .trigger-section {
            margin: 10px 0 10px 20px;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 5px;
            border-left: 3px solid #4CAF50;
        }
        .channel-section {
            margin: 10px 0;
            padding: 15px;
            background: white;
            border-radius: 5px;
            border-left: 4px solid #FF9800;
        }
        .section-title {
            color: #1976D2;
            margin: 0 0 10px 0;
            font-size: 1.2em;
            font-weight: bold;
        }
        .subsection-title {
            color: #2196F3;
            margin: 10px 0;
            font-size: 1.1em;
        }
        .info-label {
            font-weight: bold;
            color: #666;
        }
        .info-value {
            margin-left: 10px;
            color: #333;
        }
        .code-block {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 3px;
            font-family: monospace;
            white-space: pre-wrap;
            margin: 5px 0;
            border: 1px solid #e0e0e0;
        }
        .tools-list {
            margin: 5px 0;
            padding-left: 20px;
            color: #666;
        }
        .trigger-title {
            color: #4CAF50;
            font-weight: bold;
            margin: 5px 0;
        }
        .team-info-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
        }
        .close-team-info {
            position: absolute;
            top: 10px;
            right: 10px;
            padding: 5px 10px;
            background: #f44336;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
        }
        .team-info-btn {
            margin-left: 10px;
            padding: 10px 20px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .trigger-conditions {
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 5px;
            margin: 5px 0;
            padding: 5px;
            background: #fff;
            border-radius: 3px;
        }
        .trigger-condition {
            display: contents;
        }
        .trigger-condition-key {
            font-weight: bold;
            color: #4CAF50;
            padding: 2px 5px;
        }
        .trigger-condition-value {
            color: #333;
            padding: 2px 5px;
        }
        .context-section {
            margin: 10px 0;
            padding: 10px;
            background: #fff;
            border-radius: 3px;
            border: 1px solid #e0e0e0;
        }
        .context-instruction {
            white-space: pre-wrap;
            font-family: monospace;
            background: #f8f9fa;
            padding: 10px;
            border-radius: 3px;
            margin: 5px 0;
            border: 1px solid #e0e0e0;
        }
        .context-tools {
            margin: 5px 0;
        }
        .context-tool {
            display: inline-block;
            background: #e3f2fd;
            color: #1976D2;
            padding: 2px 8px;
            border-radius: 12px;
            margin: 2px;
            font-size: 0.9em;
        }
        .scratchpad-view {
            padding: 20px;
            max-width: 1600px;
            margin: 0 auto;
        }
        .scratchpad-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .scratchpad-title {
            font-size: 1.2em;
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
        .scratchpad-content {
            display: grid;
            grid-template-columns: 300px 1fr;
            font-family: monospace;
            font-size: 14px;
            line-height: 1.5;
        }
        .author-column {
            color: #666;
            font-size: 12px;
            text-align: right;
            padding-right: 16px;
            border-right: 1px solid #eee;
        }
        .content-column {
            padding-left: 16px;
            white-space: pre;
            overflow-x: auto;
        }
        .line-row {
            display: contents;
        }
        .author-cell {
            padding: 0 16px;
            height: 21px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            position: relative;
        }
        .author-cell:empty::after {
            content: "";
            position: absolute;
            left: 0;
            right: 16px;
            top: 50%;
            border-top: 1px solid #eee;
        }
        .author-cell:empty {
            background-color: #fafbfc;
        }
        .content-cell {
            padding: 0 16px;
            height: 21px;
            display: flex;
            align-items: center;
        }
        .author-cell:hover, .content-cell:hover {
            background-color: #f6f8fa;
        }
        .author-info {
            font-size: 0.8em;
            color: #888;
            margin-left: 10px;
            display: inline-block;
        }
        .scratchpad-tab-btn {
            padding: 10px 20px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-left: 10px;
        }
        .scratchpad-tab-btn:hover {
            background: #45a049;
        }
    </style>
    <script>
        function saveScrollPositions() {
            // Save panel scroll positions
            document.querySelectorAll('.panel').forEach(panel => {
                const agentId = panel.querySelector('h2').textContent;
                localStorage.setItem(`panel_scroll_${agentId}`, panel.scrollTop);
                
                // Save message section scroll positions
                const messagesDiv = panel.querySelector('.messages');
                if (messagesDiv) {
                    localStorage.setItem(`messages_scroll_${agentId}`, messagesDiv.scrollTop);
                }
            });
        }

        function restoreScrollPositions() {
            document.querySelectorAll('.panel').forEach(panel => {
                const agentId = panel.querySelector('h2').textContent;
                const savedPanelScroll = localStorage.getItem(`panel_scroll_${agentId}`);
                if (savedPanelScroll) {
                    panel.scrollTop = savedPanelScroll;
                }
                
                const messagesDiv = panel.querySelector('.messages');
                if (messagesDiv) {
                    const savedMessagesScroll = localStorage.getItem(`messages_scroll_${agentId}`);
                    if (savedMessagesScroll) {
                        messagesDiv.scrollTop = savedMessagesScroll;
                    }
                }
            });
        }

        // Save positions before refresh
        window.addEventListener('beforeunload', saveScrollPositions);
        
        // Restore positions after page load
        document.addEventListener('DOMContentLoaded', () => {
            restoreScrollPositions();
            initializeView();
        });

        function refreshPage() {
            fetchUpdates();
        }

        function initializeView() {
            const viewMode = localStorage.getItem('viewMode') || 'side';
            const lastActiveTab = localStorage.getItem('activeTab');
            
            if (viewMode === 'tab') {
                const sideView = document.getElementById('side-by-side');
                const tabView = document.getElementById('tab-view');
                const tabButtons = document.getElementById('tab-buttons');
                const toggleBtn = document.getElementById('view-toggle');
                
                sideView.style.display = 'none';
                tabView.style.display = 'block';
                tabButtons.style.display = 'block';
                toggleBtn.textContent = 'Switch to Side by Side';
                
                const tabToShow = lastActiveTab || document.querySelector('.tab-btn').getAttribute('data-agent');
                showTab(tabToShow);
            }
        }

        function toggleView() {
            const sideView = document.getElementById('side-by-side');
            const tabView = document.getElementById('tab-view');
            const tabButtons = document.getElementById('tab-buttons');
            const scratchpadView = document.getElementById('scratchpad-view');
            const toggleBtn = document.getElementById('view-toggle');
            
            scratchpadView.style.display = 'none';
            
            if (sideView.style.display === 'none') {
                sideView.style.display = 'grid';
                tabView.style.display = 'none';
                tabButtons.style.display = 'none';
                toggleBtn.textContent = 'Switch to Tab View';
                localStorage.setItem('viewMode', 'side');
            } else {
                sideView.style.display = 'none';
                tabView.style.display = 'block';
                tabButtons.style.display = 'block';
                toggleBtn.textContent = 'Switch to Side by Side';
                localStorage.setItem('viewMode', 'tab');
                const lastActiveTab = localStorage.getItem('activeTab');
                const tabToShow = lastActiveTab || document.querySelector('.tab-btn').getAttribute('data-agent');
                showTab(tabToShow);
            }
        }

        function showTab(agentId) {
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
                if (btn.getAttribute('data-agent') === agentId) {
                    btn.classList.add('active');
                }
            });
            
            document.querySelectorAll('.panel.tab').forEach(panel => {
                panel.classList.remove('active');
                if (panel.getAttribute('data-agent') === agentId) {
                    panel.classList.add('active');
                }
            });
            
            localStorage.setItem('activeTab', agentId);
        }

        let lastMessageCounts = {};

        function initializeMessageCounts() {
            document.querySelectorAll('.panel').forEach(panel => {
                const agentId = panel.querySelector('h2').textContent;
                const messages = panel.querySelectorAll('.message');
                lastMessageCounts[agentId] = messages.length;
            });
        }

        function createMessageElement(msg, agentId) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${msg.source === agentId ? 'sent' : 'received'}`;
            
            const headerDiv = document.createElement('div');
            headerDiv.className = 'message-header';
            headerDiv.textContent = `${msg.source} -> ${msg.destination}${msg.channel ? ` (${msg.channel})` : ''}:`;
            messageDiv.appendChild(headerDiv);
            
            if (msg.content) {
                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';
                contentDiv.textContent = msg.content;
                messageDiv.appendChild(contentDiv);
            }
            
            if (msg.actions) {
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'scrollable-content';
                const actionsPre = document.createElement('pre');
                actionsPre.textContent = `[Actions]\n${JSON.stringify(msg.actions, null, 2)}`;
                actionsDiv.appendChild(actionsPre);
                messageDiv.appendChild(actionsDiv);
            }
            
            if (msg.observations) {
                const obsDiv = document.createElement('div');
                obsDiv.className = 'scrollable-content';
                const obsPre = document.createElement('pre');
                obsPre.textContent = `[Observations]\n${JSON.stringify(msg.observations, null, 2)}`;
                obsDiv.appendChild(obsPre);
                messageDiv.appendChild(obsDiv);
            }
            
            return messageDiv;
        }

        function updatePanelContent(panel, newContent, newMessages) {
            const agentId = panel.querySelector('h2').textContent;
            
            // Update output content if it exists
            const outputDiv = panel.querySelector('.output');
            if (outputDiv && newContent) {
                outputDiv.querySelector('pre').textContent = newContent;
            }
            
            // Update messages
            const messagesDiv = panel.querySelector('.messages');
            if (messagesDiv && newMessages) {
                const currentCount = lastMessageCounts[agentId] || 0;
                const newCount = newMessages.length;
                
                if (newCount > currentCount) {
                    // Append only new messages
                    const wasAtBottom = messagesDiv.scrollHeight - messagesDiv.scrollTop === messagesDiv.clientHeight;
                    
                    for (let i = currentCount; i < newCount; i++) {
                        const messageElement = createMessageElement(newMessages[i], agentId);
                        messagesDiv.appendChild(messageElement);
                    }
                    
                    // Auto-scroll if was at bottom
                    if (wasAtBottom) {
                        messagesDiv.scrollTop = messagesDiv.scrollHeight;
                    }
                    
                    lastMessageCounts[agentId] = newCount;
                }
            }
        }

        async function fetchUpdates() {
            try {
                const response = await fetch('/updates');
                const data = await response.json();
                
                // Update panels
                data.panels.forEach(panelData => {
                    const panel = $(`h2:contains("${panelData.agent_id}")`).closest('.panel')[0];
                    if (panel) {
                        updatePanelContent(panel, panelData.content, panelData.messages);
                    }
                });

                // Update scratchpad view if it's visible
                const scratchpadView = document.getElementById('scratchpad-view');
                if (scratchpadView && scratchpadView.style.display === 'block') {
                    fetchScratchpads();
                }
            } catch (error) {
                console.error('Error fetching updates:', error);
            }
        }

        // Initialize message counts and start update loop
        document.addEventListener('DOMContentLoaded', () => {
            initializeMessageCounts();
            initializeView();
            
            // Auto fetch updates every 2 seconds
            setInterval(fetchUpdates, 2000);
        });

        // Add contains selector for case-insensitive text matching
        jQuery.expr[':'].contains = function(a, i, m) {
            return jQuery(a).text().toUpperCase()
                .indexOf(m[3].toUpperCase()) >= 0;
        };

        async function showTeamInfo() {
            try {
                const response = await fetch('/team_info');
                const data = await response.json();
                let content = '';
                
                // Display Teams
                content += '<h3 class="section-title">Teams</h3>';
                data.teams.forEach(team => {
                    content += `<div class="team-section">`;
                    content += `<div class="subsection-title">Team: ${team.name}</div>`;
                    
                    // Show collaboration info
                    if (typeof team.collaboration === 'object') {
                        content += `<div><span class="info-label">Collaboration:</span>`;
                        content += `<span class="info-value">${team.collaboration.type}</span>`;
                        if (team.collaboration.coordinator) {
                            content += `<br><span class="info-label">Coordinator:</span>`;
                            content += `<span class="info-value">${team.collaboration.coordinator}</span>`;
                        }
                        content += `</div>`;
                    } else {
                        content += `<div><span class="info-label">Collaboration:</span>`;
                        content += `<span class="info-value">${team.collaboration}</span></div>`;
                    }
                    
                    // Show agents
                    content += `<div class="subsection-title">Agents:</div>`;
                    team.agents.forEach(agent => {
                        content += `<div class="agent-section">`;
                        content += `<div><span class="info-label">Name:</span>`;
                        content += `<span class="info-value">${agent.name}</span></div>`;
                        content += `<div><span class="info-label">Type:</span>`;
                        content += `<span class="info-value">${agent.type}</span></div>`;
                        
                        if (agent.instruction) {
                            content += `<div><span class="info-label">Instruction:</span></div>`;
                            content += `<div class="code-block">${agent.instruction}</div>`;
                        }
                        
                        if (agent.tools && agent.tools.length > 0) {
                            content += `<div><span class="info-label">Tools:</span></div>`;
                            content += `<ul class="tools-list">`;
                            agent.tools.forEach(tool => {
                                content += `<li>${tool}</li>`;
                            });
                            content += `</ul>`;
                        }
                        
                        if (agent.triggers && agent.triggers.length > 0) {
                            content += `<div class="subsection-title">Triggers:</div>`;
                            agent.triggers.forEach(trigger => {
                                content += `<div class="trigger-section">`;
                                content += `<div class="trigger-title">${trigger.type}</div>`;
                                
                                // Display conditions in a grid
                                content += `<div><span class="info-label">Conditions:</span></div>`;
                                content += `<div class="trigger-conditions">`;
                                Object.entries(trigger.conditions).forEach(([key, value]) => {
                                    content += `<div class="trigger-condition">`;
                                    content += `<div class="trigger-condition-key">${key}:</div>`;
                                    content += `<div class="trigger-condition-value">${value}</div>`;
                                    content += `</div>`;
                                });
                                content += `</div>`;
                                
                                // Display context in a structured way
                                content += `<div><span class="info-label">Context:</span></div>`;
                                content += `<div class="context-section">`;
                                if (trigger.context.instruction) {
                                    content += `<div><span class="info-label">Instruction:</span></div>`;
                                    content += `<div class="context-instruction">${trigger.context.instruction}</div>`;
                                }
                                if (trigger.context.tools && trigger.context.tools.length > 0) {
                                    content += `<div><span class="info-label">Tools:</span></div>`;
                                    content += `<div class="context-tools">`;
                                    trigger.context.tools.forEach(tool => {
                                        content += `<span class="context-tool">${tool}</span>`;
                                    });
                                    content += `</div>`;
                                }
                                content += `</div>`;
                                
                                content += `</div>`;
                            });
                        }
                        
                        content += `</div>`;
                    });
                    content += `</div>`;
                });
                
                // Display Channels
                if (data.channels.length > 0) {
                    content += '<h3 class="section-title">Channels</h3>';
                    data.channels.forEach(channel => {
                        content += `<div class="channel-section">`;
                        content += `<div><span class="info-label">Name:</span>`;
                        content += `<span class="info-value">${channel.name}</span></div>`;
                        content += `<div><span class="info-label">Members:</span>`;
                        content += `<span class="info-value">${channel.members.join(', ')}</span></div>`;
                        content += `</div>`;
                    });
                }
                
                document.getElementById('teamInfoContent').innerHTML = content;
                document.getElementById('teamInfoOverlay').style.display = 'block';
                document.getElementById('teamInfo').style.display = 'block';
            } catch (error) {
                console.error('Error fetching team info:', error);
            }
        }

        function hideTeamInfo() {
            document.getElementById('teamInfoOverlay').style.display = 'none';
            document.getElementById('teamInfo').style.display = 'none';
        }

        function showScratchpadTab() {
            // Hide all other views
            document.getElementById('side-by-side').style.display = 'none';
            document.getElementById('tab-view').style.display = 'none';
            document.getElementById('tab-buttons').style.display = 'none';
            document.getElementById('scratchpad-view').style.display = 'block';
            
            // Fetch and display scratchpads
            fetchScratchpads();
        }

        function fetchScratchpads() {
            fetch('/scratchpads')
                .then(response => response.json())
                .then(data => {
                    let content = '';
                    data.scratchpads.forEach(scratchpad => {
                        content += `<div class="scratchpad-card">`;
                        content += `<div class="scratchpad-title">${scratchpad.id}</div>`;
                        content += `<div class="scratchpad-content">`;
                        
                        // Author column
                        content += `<div class="author-column">`;
                        let lastAuthor = null;
                        scratchpad.lines.forEach((line, index) => {
                            content += `<div class="author-cell">`;
                            if (line.last_modified_by !== lastAuthor) {
                                content += `by ${line.last_modified_by}`;
                                lastAuthor = line.last_modified_by;
                            }
                            content += `</div>`;
                        });
                        content += `</div>`;
                        
                        // Content column
                        content += `<div class="content-column">`;
                        scratchpad.lines.forEach((line, index) => {
                            content += `<div class="content-cell">`;
                            content += line.content;
                            content += `</div>`;
                        });
                        content += `</div>`;
                        
                        content += `</div></div>`;
                    });
                    document.getElementById('scratchpadContent').innerHTML = content;
                });
        }
    </script>
</head>
<body>
    <div class="header">
        <h1>Chorus Visual Debugger</h1>
        <div>
            <button id="view-toggle" class="view-toggle" onclick="toggleView()">Switch to Tab View</button>
            <button class="scratchpad-tab-btn" onclick="showScratchpadTab()">Show Scratchpads</button>
            <button class="team-info-btn" onclick="showTeamInfo()">Show Team Settings</button>
        </div>
    </div>

    <div class="content">
        <!-- Scratchpad View -->
        <div id="scratchpad-view" class="scratchpad-view" style="display: none;">
            <div id="scratchpadContent"></div>
        </div>

        <!-- Tab Buttons -->
        <div id="tab-buttons" class="tab-buttons">
            {% for panel in panels %}
            <button class="tab-btn" data-agent="{{ panel.agent_id }}" onclick="showTab('{{ panel.agent_id }}')">
                {{ panel.agent_id }}
            </button>
            {% endfor %}
        </div>

        <!-- Side by Side View -->
        <div id="side-by-side" class="side-by-side">
            {% for panel in panels %}
            <div class="panel {% if panel.agent_id == 'Global Messages' %}global-messages{% endif %}">
                <h2>{{ panel.agent_id }}</h2>
                <div class="panel-content">
                    {% if panel.content %}
                    <div class="output">
                        <pre>{{ panel.content }}</pre>
                    </div>
                    {% endif %}
                    <div class="messages {% if panel.agent_id == 'Global Messages' %}global-messages{% endif %}">
                        {% for msg in panel.messages %}
                            {% if msg.source == panel.agent_id %}
                            <div class="message sent">
                                <div class="message-header">{{ msg.source }} -> {{ msg.destination }}{% if msg.channel %} ({{ msg.channel }}){% endif %}:</div>
                                {% if msg.content %}
                                <div class="message-content">
                                {{ msg.content }}
                                </div>
                                {% endif %}
                                {% if msg.actions %}
                                <div class="scrollable-content">
                                <pre>[Actions]\n{{ msg.actions | tojson(indent=2) }}</pre>
                                </div>
                                {% endif %}
                                {% if msg.observations %}
                                <div class="scrollable-content">
                                <pre>[Observations]\n{{ msg.observations | tojson(indent=2) }}</pre>
                                </div>
                                {% endif %}
                            </div>
                            {% else %}
                            <div class="message received">
                                <div class="message-header">{{ msg.source }} -> {{ msg.destination }}{% if msg.channel %} ({{ msg.channel }}){% endif %}:</div>
                                {% if msg.content %}
                                <div class="message-content">
                                {{ msg.content }}
                                </div>
                                {% endif %}
                                {% if msg.actions %}
                                <div class="scrollable-content">
                                <pre>[Actions]\n{{ msg.actions | tojson(indent=2) }}</pre>
                                </div>
                                {% endif %}
                                {% if msg.observations %}
                                <div class="scrollable-content">
                                <pre>[Observations]\n{{ msg.observations | tojson(indent=2) }}</pre>
                                </div>
                                {% endif %}
                            </div>
                            {% endif %}
                        {% endfor %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <!-- Tab View -->
        <div id="tab-view" class="tab-view">
            {% for panel in panels %}
            <div class="panel tab {% if panel.agent_id == 'Global Messages' %}global-messages{% endif %}" data-agent="{{ panel.agent_id }}">
                <h2>{{ panel.agent_id }}</h2>
                <div class="panel-content">
                    {% if panel.content %}
                    <div class="output">
                        <pre>{{ panel.content }}</pre>
                    </div>
                    {% endif %}
                    <div class="messages {% if panel.agent_id == 'Global Messages' %}global-messages{% endif %}">
                        {% for msg in panel.messages %}
                            {% if msg.source == panel.agent_id %}
                            <div class="message sent">
                                <div class="message-header">{{ msg.source }} -> {{ msg.destination }}{% if msg.channel %} ({{ msg.channel }}){% endif %}:</div>
                                {% if msg.content %}
                                <div class="message-content">
                                {{ msg.content }}
                                </div>
                                {% endif %}
                                {% if msg.actions %}
                                <div class="scrollable-content">
                                <pre>[Actions]\n{{ msg.actions | tojson(indent=2) }}</pre>
                                </div>
                                {% endif %}
                                {% if msg.observations %}
                                <div class="scrollable-content">
                                <pre>[Observations]\n{{ msg.observations | tojson(indent=2) }}</pre>
                                </div>
                                {% endif %}
                            </div>
                            {% else %}
                            <div class="message received">
                                <div class="message-header">{{ msg.source }} -> {{ msg.destination }}{% if msg.channel %} ({{ msg.channel }}){% endif %}:</div>
                                {% if msg.content %}
                                <div class="message-content">
                                {{ msg.content }}
                                </div>
                                {% endif %}
                                {% if msg.actions %}
                                <div class="scrollable-content">
                                <pre>[Actions]\n{{ msg.actions | tojson(indent=2) }}</pre>
                                </div>
                                {% endif %}
                                {% if msg.observations %}
                                <div class="scrollable-content">
                                <pre>[Observations]\n{{ msg.observations | tojson(indent=2) }}</pre>
                                </div>
                                {% endif %}
                            </div>
                            {% endif %}
                        {% endfor %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <button class="refresh-btn" onclick="refreshPage()">Refresh</button>

    <div class="team-info-overlay" id="teamInfoOverlay"></div>
    <div class="team-info" id="teamInfo">
        <button class="close-team-info" onclick="hideTeamInfo()">×</button>
        <h2>Team Settings</h2>
        <div id="teamInfoContent"></div>
    </div>
</body>
</html>
'''


class VisualDebugger:
    def __init__(self, port: int = 5000):
        self.app = Flask(__name__)
        # Disable Flask's default logger
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        self.port = port
        self.log_files: Dict[str, str] = {}
        self.teams: List = []
        self.channels: List = []
        self._states: Dict = {}  # Store agent and team states
        self._setup_routes()
        self.server_thread: Optional[threading.Thread] = None
        
    def register_state(self, identifier: str, state):
        """Register an agent or team state with the debugger."""
        self._states[identifier] = state

    def _get_team_state(self, team) -> Optional['TeamState']:
        """Get the team state if it exists."""
        team_agent_id = f"team:{team._name}"
        return self._states.get(team_agent_id)

    def _get_agent_messages(self, messages_log_file: str, agent_id: str) -> List[Dict]:
        """Get sent and received messages for an agent."""
        if not os.path.exists(messages_log_file):
            return []
        
        messages = []
        try:
            with open(messages_log_file, 'r') as f:
                for line in f:
                    try:
                        msg = json.loads(line.strip())
                        if "source" not in msg or "destination" not in msg or "content" not in msg:
                            continue
                        if msg['source'] == agent_id or msg['destination'] == agent_id:
                            messages.append(msg)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            return []
        return messages

    def _get_all_messages(self, messages_log_file: str) -> List[Dict]:
        """Get all messages excluding self-messages and messages with actions/observations."""
        if not os.path.exists(messages_log_file):
            return []
        
        messages = []
        try:
            with open(messages_log_file, 'r') as f:
                for line in f:
                    try:
                        msg = json.loads(line.strip())
                        if "source" not in msg or "destination" not in msg or "content" not in msg:
                            continue
                        # Exclude self-messages and messages with actions/observations
                        if msg['source'] != msg['destination'] and not msg['actions'] and not msg['observations']:
                            messages.append(msg)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            return []
        return messages

    def _get_team_scratchpads(self, team) -> List[Dict]:
        """Get all scratchpads from a team's scratchpad service."""
        scratchpads: List = []
        try:
            team_state = self._get_team_state(team)
            if not team_state:
                print(f"No state found for team agent team:{team._name}")
                return scratchpads

            for service in team._services:
                if service.__class__.__name__ == "TeamScratchpad":
                    scratchpads_dict = team_state.get_service_data_store(service.get_name()).get("scratchpads", {})
                    for scratchpad_id, lines in scratchpads_dict.items():
                        scratchpad_content = {
                            "id": scratchpad_id,
                            "lines": [
                                {
                                    "content": line.content,
                                    "last_modified_by": line.last_modified_by,
                                    "last_modified_time": line.last_modified_time.isoformat()
                                }
                                for line in lines
                            ]
                        }
                        scratchpads.append(scratchpad_content)
        except Exception as e:
            print(f"Error getting scratchpads: {str(e)}")
            import traceback
            print(traceback.format_exc())
        return scratchpads

    def _setup_routes(self):
        @self.app.route('/')
        def home():
            panels = []
            messages_log_file = next((log_file for agent_id, log_file in self.log_files.items() if agent_id == 'messages'), None)
            
            # Add Global Messages panel first
            if messages_log_file:
                global_messages = self._get_all_messages(messages_log_file)
                panels.append({
                    'agent_id': 'Global Messages',
                    'content': '',
                    'messages': global_messages,
                    'last_message_count': len(global_messages)
                })

            # Add Scratchpads panel if any team has scratchpad service
            for team in self.teams:
                has_scratchpad = any(service.__class__.__name__ == "TeamScratchpad" for service in team._services)
                if has_scratchpad:
                    scratchpads = self._get_team_scratchpads(team)
                    panels.append({
                        'agent_id': f'{team._name} Scratchpads',
                        'content': json.dumps(scratchpads, indent=2),
                        'messages': [],
                        'last_message_count': 0
                    })
            
            # Add agent panels
            for agent_id, log_file in self.log_files.items():
                if agent_id == 'messages':
                    continue
                    
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                except:
                    content = "No log data available yet..."
                    
                agent_messages = []
                if messages_log_file:
                    agent_messages = self._get_agent_messages(messages_log_file, agent_id)
                
                panels.append({
                    'agent_id': agent_id,
                    'content': content,
                    'messages': agent_messages,
                    'last_message_count': len(agent_messages)
                })
            
            return render_template_string(VISUAL_TEMPLATE, panels=panels)
            
        @self.app.route('/updates')
        def get_updates():
            panels = []
            messages_log_file = next((log_file for agent_id, log_file in self.log_files.items() if agent_id == 'messages'), None)
            
            # Add Global Messages panel first
            if messages_log_file:
                global_messages = self._get_all_messages(messages_log_file)
                panels.append({
                    'agent_id': 'Global Messages',
                    'content': '',
                    'messages': global_messages
                })

            # Add Scratchpads panel if any team has scratchpad service
            for team in self.teams:
                has_scratchpad = any(service.__class__.__name__ == "TeamScratchpad" for service in team._services)
                if has_scratchpad:
                    scratchpads = self._get_team_scratchpads(team)
                    panels.append({
                        'agent_id': f'{team._name} Scratchpads',
                        'content': json.dumps(scratchpads, indent=2),
                        'messages': []
                    })
            
            # Add agent panels
            for agent_id, log_file in self.log_files.items():
                if agent_id == 'messages':
                    continue
                    
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                except:
                    content = "No log data available yet..."
                    
                agent_messages = []
                if messages_log_file:
                    agent_messages = self._get_agent_messages(messages_log_file, agent_id)
                
                panels.append({
                    'agent_id': agent_id,
                    'content': content,
                    'messages': agent_messages
                })
            
            return {'panels': panels}

        @self.app.route('/team_info')
        def get_team_info():
            try:
                team_data = self._get_team_info()
                return jsonify(team_data)
            except Exception as e:
                print(f"Error in team_info route: {str(e)}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/scratchpads')
        def get_scratchpads():
            try:
                all_scratchpads = []
                for team in self.teams:
                    scratchpads = self._get_team_scratchpads(team)
                    all_scratchpads.extend(scratchpads)
                return jsonify({'scratchpads': all_scratchpads})
            except Exception as e:
                print(f"Error in scratchpads route: {str(e)}")
                return jsonify({'error': str(e)}), 500

    def start(self):
        def run_flask():
            # Disable Flask access logging
            self.app.run(port=self.port, debug=False, use_reloader=False)
            
        self.server_thread = threading.Thread(target=run_flask)
        self.server_thread.daemon = True
        self.server_thread.start()
        # Wait a bit for the server to start
        time.sleep(1)
        # Open browser
        webbrowser.open(f'http://localhost:{self.port}')
        
    def add_agent_log(self, agent_id: str, log_file: str):
        self.log_files[agent_id] = log_file 

    def add_team(self, team):
        """Add a team to be visualized."""
        self.teams.append(team)

    def add_channel(self, channel):
        """Add a channel to be visualized."""
        self.channels.append(channel)

    def _get_team_info(self):
        """Get structured information about teams, agents, and channels."""
        try:
            team_info = []
            for team in self.teams:
                try:
                    # Get team collaboration info
                    collaboration_info = 'None'
                    if hasattr(team, 'collaboration') and team.collaboration:
                        try:
                            collaboration_info = {
                                'type': team.collaboration.__class__.__name__,
                                'coordinator': team.collaboration.coordinator if hasattr(team.collaboration, 'coordinator') else None
                            }
                        except:
                            collaboration_info = team.collaboration.__class__.__name__

                    team_data = {
                        'name': team._name if hasattr(team, '_name') else str(team),
                        'collaboration': collaboration_info,
                        'agents': []
                    }
                    
                    # Get agents info
                    for agent in team.get_agents() if hasattr(team, 'get_agents') else []:
                        try:
                            agent_data = {
                                'name': agent.get_name() if hasattr(agent, 'get_name') else str(agent),
                                'type': agent.__class__.__name__,
                                'instruction': agent.get_instruction() if hasattr(agent, 'get_instruction') else None,
                                'triggers': []
                            }
                            
                            # Get tools if available
                            if hasattr(agent, 'get_tools') and agent.get_tools():
                                agent_data['tools'] = [
                                    t.get_schema().tool_name for t in agent.get_tools()
                                ]
                            
                            # Get triggers and contexts if available
                            if hasattr(agent, '_context_switchers'):
                                for trigger, context in agent._context_switchers:
                                    try:
                                        # Get trigger conditions
                                        conditions = {}
                                        for k, v in trigger.__dict__.items():
                                            if v is not None and not k.startswith('_'):
                                                if isinstance(v, (str, int, float, bool, list, dict)):
                                                    conditions[k] = v
                                                else:
                                                    conditions[k] = str(v)

                                        # Get context info
                                        context_info = {
                                            'instruction': context.agent_instruction if hasattr(context, 'agent_instruction') else None,
                                            'tools': []
                                        }
                                        if hasattr(context, 'tools') and context.tools:
                                            context_info['tools'] = [
                                                t.get_schema().tool_name for t in context.tools
                                            ]

                                        trigger_data = {
                                            'type': trigger.__class__.__name__,
                                            'conditions': conditions,
                                            'context': context_info
                                        }
                                        agent_data['triggers'].append(trigger_data)
                                    except Exception as e:
                                        print(f"Error processing trigger for agent {agent_data['name']}: {str(e)}")
                                        continue
                            
                            team_data['agents'].append(agent_data)
                        except Exception as e:
                            print(f"Error processing agent in team {team_data['name']}: {str(e)}")
                            continue
                    
                    team_info.append(team_data)
                except Exception as e:
                    print(f"Error processing team: {str(e)}")
                    continue
            
            channel_info = []
            for channel in self.channels:
                try:
                    channel_info.append({
                        'name': channel.name if hasattr(channel, 'name') else str(channel),
                        'members': list(channel.members) if hasattr(channel, 'members') else []
                    })
                except Exception as e:
                    print(f"Error processing channel: {str(e)}")
                    continue
            
            return {'teams': team_info, 'channels': channel_info}
        except Exception as e:
            print(f"Error in _get_team_info: {str(e)}")
            return {'teams': [], 'channels': []} 