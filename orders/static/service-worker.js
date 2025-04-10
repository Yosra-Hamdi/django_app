// Chargement sécurisé du SDK Pusher
try {
    importScripts("https://js.pusher.com/beams/service-worker.js");
} catch (e) {
    console.warn("Erreur chargement SDK Pusher:", e);
}

// Nouvelle fonction pour diffuser aux clients
function broadcastToClients(message) {
    self.clients.matchAll({ 
        type: "window", 
        includeUncontrolled: true 
    }).then(clients => {
        clients.forEach(client => {
            console.log("Envoi message au client:", client.url);
            client.postMessage(message);
        });
    });
}

self.addEventListener('push', (event) => {
    // Parsing sécurisé des données
    let payload;
    try {
        payload = event.data?.json() || {};
    } catch (e) {
        payload = {
            notification: { title: "Nouvelle commande", body: "" },
            data: {}
        };
    }

    const title = payload.notification?.title || "Nouvelle commande";
    const body = payload.notification?.body || "";
    const order_id = payload.data?.order_id || null;

    // Préparer le message pour les clients
    const clientMessage = {
        type: "NEW_NOTIFICATION",
        notification: { title, body },
        data: { order_id }
    };

    // Diffuser immédiatement aux clients avant tout traitement
    broadcastToClients(clientMessage);

    event.waitUntil(
        Promise.all([
            // Enregistrement en base
            fetch('/graphql/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: `
                        mutation CreateNotification($title: String!, $body: String!, $orderId: String) {
                            createNotification(
                                title: $title
                                body: $body
                                orderId: $orderId
                            ) {
                                notification {
                                    id
                                }
                            }
                        }
                    `,
                    variables: {
                        title: title,
                        body: body,
                        orderId: order_id
                    }
                })
            }).catch(err => console.error("Erreur GraphQL:", err)),
            
            // Notification système
            self.registration.showNotification(title, {
                body: body,
                data: { order_id },
                icon: '/icons/icon.png',
                vibrate: [200, 100, 200] // Ajout de vibration pour mobile
            }),
            
            // Sauvegarde IndexedDB
            saveToIndexedDB({
                title,
                body,
                order_id,
                timestamp: new Date().toISOString()
            })
        ])
    );
});

// Fonction IndexedDB inchangée
function saveToIndexedDB(notification) {
    return new Promise((resolve) => {
        const request = indexedDB.open('NotificationsDB', 1);
        request.onupgradeneeded = (e) => {
            const db = e.target.result;
            if (!db.objectStoreNames.contains('notifications')) {
                db.createObjectStore('notifications', { keyPath: 'timestamp' });
            }
        };
    
        request.onsuccess = (e) => {
            const db = e.target.result;
            const tx = db.transaction('notifications', 'readwrite');
            const store = tx.objectStore('notifications');
            store.put(notification);
            resolve();
        };
    
        request.onerror = (e) => {
            console.error('IndexedDB error:', e);
            resolve();
        };
    });
}

// Gestion du clic
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const url = event.notification.data?.order_id 
        ? `/orders/${event.notification.data.order_id}` 
        : '/orders/dashboard';
    
    event.waitUntil(
        clients.matchAll({ type: 'window' })
            .then(windowClients => {
                const client = windowClients.find(c => c.url.includes(url));
                return client 
                    ? client.focus() 
                    : clients.openWindow(url);
            })
    );
});