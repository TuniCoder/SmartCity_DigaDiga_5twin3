/**
 * SmartCity Visualization Library
 * Bibliothèque JavaScript pour la visualisation des données RDF et l'interaction avec l'API
 */

class SmartCityVisualization {
    constructor() {
        this.apiBaseUrl = '/api/';
        this.currentData = null;
        this.charts = {};
    }

    /**
     * Initialise la visualisation
     */
    init() {
        console.log('SmartCity Visualization initialized');
        this.setupEventListeners();
        this.loadInitialData();
    }

    /**
     * Configure les écouteurs d'événements
     */
    setupEventListeners() {
        // Gestion des requêtes IA
        const aiForm = document.getElementById('aiQueryForm');
        if (aiForm) {
            aiForm.addEventListener('submit', this.handleAIQuery.bind(this));
        }

        // Gestion des clics sur les entités
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('entity-link')) {
                e.preventDefault();
                this.showEntityDetails(e.target.getAttribute('data-uri'));
            }
        });

        // Recherche en temps réel
        const searchInput = document.getElementById('realTimeSearch');
        if (searchInput) {
            let timeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.performSearch(e.target.value);
                }, 500);
            });
        }
    }

    /**
     * Charge les données initiales
     */
    async loadInitialData() {
        try {
            const response = await fetch(this.apiBaseUrl + 'status/');
            const data = await response.json();
            
            if (data.success) {
                this.updateDashboard(data.statistics);
            }
        } catch (error) {
            console.error('Erreur lors du chargement des données:', error);
        }
    }

    /**
     * Met à jour le tableau de bord avec les statistiques
     */
    updateDashboard(statistics) {
        // Mettre à jour les compteurs
        this.updateCounters(statistics);
        
        // Créer les graphiques
        if (statistics.entities_by_type) {
            this.createEntitiesChart(statistics.entities_by_type);
        }
    }

    /**
     * Met à jour les compteurs affichés
     */
    updateCounters(stats) {
        const counters = {
            'total-triples': stats.total_triples,
            'total-classes': stats.classes,
            'total-properties': stats.properties,
            'total-individuals': stats.individuals
        };

        Object.entries(counters).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                this.animateCounter(element, value);
            }
        });
    }

    /**
     * Anime un compteur numérique
     */
    animateCounter(element, targetValue) {
        const duration = 1000;
        const startValue = 0;
        const increment = targetValue / (duration / 16);
        let currentValue = startValue;

        const timer = setInterval(() => {
            currentValue += increment;
            if (currentValue >= targetValue) {
                element.textContent = targetValue;
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(currentValue);
            }
        }, 16);
    }

    /**
     * Crée un graphique des entités
     */
    createEntitiesChart(entitiesData) {
        const canvas = document.getElementById('entitiesChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        
        // Détruire le graphique existant s'il y en a un
        if (this.charts.entities) {
            this.charts.entities.destroy();
        }

        const labels = Object.keys(entitiesData);
        const data = Object.values(entitiesData);
        const colors = [
            '#3498db', '#e74c3c', '#2ecc71', '#f39c12',
            '#9b59b6', '#1abc9c', '#34495e', '#e67e22'
        ];

        this.charts.entities = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Gère les requêtes IA
     */
    async handleAIQuery(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const question = formData.get('question');
        
        if (!question.trim()) {
            this.showAlert('Veuillez saisir une question', 'warning');
            return;
        }

        const submitBtn = event.target.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        
        // Afficher le loader
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Traitement...';
        submitBtn.disabled = true;

        try {
            const response = await fetch(this.apiBaseUrl + 'ask/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ question: question })
            });

            const data = await response.json();
            
            if (data.success) {
                this.displayQueryResults(data);
                this.showAlert(`Requête exécutée avec succès! ${data.results_count} résultat(s) trouvé(s).`, 'success');
            } else {
                this.showAlert(`Erreur: ${data.error}`, 'danger');
                if (data.suggestions) {
                    this.showSuggestions(data.suggestions);
                }
            }
        } catch (error) {
            console.error('Erreur lors de la requête IA:', error);
            this.showAlert('Erreur de communication avec le serveur', 'danger');
        } finally {
            // Restaurer le bouton
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }

    /**
     * Affiche les résultats d'une requête
     */
    displayQueryResults(data) {
        const resultsContainer = document.getElementById('queryResults');
        if (!resultsContainer) return;

        let html = `
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <span><i class="fas fa-table"></i> Résultats - ${data.explanation}</span>
                    <span class="badge bg-success">${data.results_count} résultat(s)</span>
                </div>
                <div class="card-body">
        `;

        // Afficher la requête SPARQL générée
        if (data.sparql_query) {
            html += `
                <details class="mb-3">
                    <summary><i class="fas fa-code"></i> Requête SPARQL générée</summary>
                    <pre class="sparql-query mt-2">${this.escapeHtml(data.sparql_query)}</pre>
                </details>
            `;
        }

        // Afficher les résultats
        if (data.results && data.results.length > 0) {
            html += this.generateResultsTable(data.results);
            
            // Boutons d'export
            html += `
                <div class="text-end mt-3">
                    <button class="btn btn-outline-primary btn-sm" onclick="smartCity.exportResults('csv')">
                        <i class="fas fa-download"></i> CSV
                    </button>
                    <button class="btn btn-outline-secondary btn-sm" onclick="smartCity.exportResults('json')">
                        <i class="fas fa-download"></i> JSON
                    </button>
                </div>
            `;
        } else {
            html += '<p class="text-muted text-center">Aucun résultat trouvé.</p>';
        }

        html += '</div></div>';
        resultsContainer.innerHTML = html;
        
        // Sauvegarder les résultats pour l'export
        this.currentData = data.results;
    }

    /**
     * Génère un tableau HTML pour les résultats
     */
    generateResultsTable(results) {
        if (!results || results.length === 0) return '';

        const headers = Object.keys(results[0]);
        
        let html = `
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead>
                        <tr>
        `;
        
        headers.forEach(header => {
            html += `<th><i class="fas fa-tag"></i> ${header}</th>`;
        });
        
        html += `
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        results.forEach(row => {
            html += '<tr>';
            headers.forEach(header => {
                const value = row[header] || '';
                if (this.isURI(value)) {
                    const displayValue = this.extractLocalName(value);
                    html += `
                        <td>
                            <span class="badge bg-light text-dark entity-link" 
                                  data-uri="${this.escapeHtml(value)}" 
                                  title="${this.escapeHtml(value)}">
                                ${this.escapeHtml(displayValue)}
                            </span>
                        </td>
                    `;
                } else {
                    html += `<td>${this.escapeHtml(value)}</td>`;
                }
            });
            html += '</tr>';
        });
        
        html += '</tbody></table></div>';
        return html;
    }

    /**
     * Effectue une recherche
     */
    async performSearch(keyword) {
        if (!keyword || keyword.length < 2) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}search/?q=${encodeURIComponent(keyword)}`);
            const data = await response.json();
            
            if (data.success) {
                this.displaySearchResults(data.results, keyword);
            }
        } catch (error) {
            console.error('Erreur lors de la recherche:', error);
        }
    }

    /**
     * Affiche les résultats de recherche
     */
    displaySearchResults(results, keyword) {
        const container = document.getElementById('searchResults');
        if (!container) return;

        if (results.length === 0) {
            container.innerHTML = `<p class="text-muted">Aucun résultat pour "${keyword}"</p>`;
            return;
        }

        let html = `<h6>Résultats pour "${keyword}" (${results.length})</h6>`;
        html += '<div class="list-group">';
        
        results.slice(0, 10).forEach(result => {
            const subject = this.extractLocalName(result.subject || '');
            const object = this.extractLocalName(result.object || '');
            
            html += `
                <div class="list-group-item">
                    <h6 class="mb-1">${this.escapeHtml(subject)}</h6>
                    <p class="mb-1">${this.escapeHtml(object)}</p>
                    <small class="text-muted">${this.escapeHtml(result.type || '')}</small>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
    }

    /**
     * Affiche les détails d'une entité
     */
    async showEntityDetails(uri) {
        const modal = document.getElementById('entityDetailsModal');
        if (!modal) return;

        const modalTitle = modal.querySelector('.modal-title');
        const modalBody = modal.querySelector('.modal-body');
        
        modalTitle.innerHTML = '<i class="fas fa-info-circle"></i> Chargement...';
        modalBody.innerHTML = '<div class="text-center"><div class="spinner-border text-primary"></div></div>';
        
        // Afficher le modal
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();

        try {
            const response = await fetch(`/ajax/entity-details/${encodeURIComponent(uri)}/`);
            const data = await response.json();
            
            if (data.success) {
                const entityName = this.extractLocalName(uri);
                modalTitle.innerHTML = `<i class="fas fa-info-circle"></i> ${entityName}`;
                
                let html = '<div class="table-responsive"><table class="table table-striped">';
                html += '<thead><tr><th>Propriété</th><th>Valeur</th></tr></thead><tbody>';
                
                Object.entries(data.details).forEach(([prop, value]) => {
                    html += `<tr><td><strong>${this.escapeHtml(prop)}</strong></td><td>${this.escapeHtml(value)}</td></tr>`;
                });
                
                html += '</tbody></table></div>';
                modalBody.innerHTML = html;
            } else {
                modalBody.innerHTML = `<div class="alert alert-danger">Erreur: ${data.error}</div>`;
            }
        } catch (error) {
            console.error('Erreur lors de la récupération des détails:', error);
            modalBody.innerHTML = '<div class="alert alert-danger">Erreur de communication</div>';
        }
    }

    /**
     * Exporte les résultats
     */
    exportResults(format) {
        if (!this.currentData || this.currentData.length === 0) {
            this.showAlert('Aucune donnée à exporter', 'warning');
            return;
        }

        if (format === 'csv') {
            this.exportToCSV(this.currentData);
        } else if (format === 'json') {
            this.exportToJSON(this.currentData);
        }
    }

    /**
     * Exporte au format CSV
     */
    exportToCSV(data) {
        const headers = Object.keys(data[0]);
        let csv = headers.join(',') + '\n';
        
        data.forEach(row => {
            const values = headers.map(header => {
                const value = row[header] || '';
                return `"${value.toString().replace(/"/g, '""')}"`;
            });
            csv += values.join(',') + '\n';
        });
        
        this.downloadFile(csv, 'smartcity-results.csv', 'text/csv');
    }

    /**
     * Exporte au format JSON
     */
    exportToJSON(data) {
        const json = JSON.stringify(data, null, 2);
        this.downloadFile(json, 'smartcity-results.json', 'application/json');
    }

    /**
     * Télécharge un fichier
     */
    downloadFile(content, filename, contentType) {
        const blob = new Blob([content], { type: contentType });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    /**
     * Affiche une alerte
     */
    showAlert(message, type = 'info') {
        // Créer une alerte Bootstrap
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${this.escapeHtml(message)}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Injecter dans le container d'alertes ou créer un
        let container = document.getElementById('alertsContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'alertsContainer';
            container.className = 'position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1050';
            document.body.appendChild(container);
        }
        
        const alertElement = document.createElement('div');
        alertElement.innerHTML = alertHtml;
        container.appendChild(alertElement.firstElementChild);
        
        // Supprimer automatiquement après 5 secondes
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, 5000);
    }

    /**
     * Fonctions utilitaires
     */
    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }

    isURI(str) {
        return str && (str.startsWith('http://') || str.startsWith('https://'));
    }

    extractLocalName(uri) {
        if (!uri) return '';
        const parts = uri.split('#');
        if (parts.length > 1) return parts[parts.length - 1];
        const pathParts = uri.split('/');
        return pathParts[pathParts.length - 1];
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialiser la bibliothèque
const smartCity = new SmartCityVisualization();

// Initialiser quand le DOM est prêt
document.addEventListener('DOMContentLoaded', () => {
    smartCity.init();
});

// Rendre disponible globalement
window.smartCity = smartCity;