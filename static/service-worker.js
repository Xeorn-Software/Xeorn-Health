// Service Worker for RWANA Health Voice Assistant
const CACHE_NAME = 'rwana-health-app-v1';
const urlsToCache = [
  '/',
  '/static/service-worker.js',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js',
  'https://cdn.jsdelivr.net/npm/recordrtc/RecordRTC.min.js',
  'https://cdn.jsdelivr.net/npm/chart.js'
];

// Install event - cache resources
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Fetch event - serve from cache, fall back to network
self.addEventListener('fetch', event => {
  // Only handle GET requests
  if (event.request.method !== 'GET') return;
  
  // Skip some specific URLs that should never be cached
  const url = new URL(event.request.url);
  if (url.pathname.startsWith('/process_text') || 
      url.pathname.startsWith('/process_audio') ||
      url.pathname.startsWith('/send_sms')) {
    return;
  }
  
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - return the response
        if (response) {
          return response;
        }
        
        // Clone the request since it's a one-time use stream
        const fetchRequest = event.request.clone();
        
        return fetch(fetchRequest).then(response => {
          // Check if we received a valid response
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }
          
          // Clone the response since it's a one-time use stream
          const responseToCache = response.clone();
          
          caches.open(CACHE_NAME)
            .then(cache => {
              cache.put(event.request, responseToCache);
            });
            
          return response;
        }).catch(error => {
          // If both cache and network fail, return a simple offline page
          if (event.request.mode === 'navigate') {
            return new Response(
              '<html><body><h1>You are offline</h1><p>The RWANA Health Voice Assistant needs an internet connection to work fully.</p></body></html>', 
              { headers: { 'Content-Type': 'text/html' } }
            );
          }
          
          return new Response('Offline');
        });
      })
  );
});

// Background sync for offline operations
self.addEventListener('sync', event => {
  if (event.tag === 'sync-health-data') {
    event.waitUntil(syncHealthData());
  }
});

// Function to sync health data when back online
async function syncHealthData() {
  // Implement your sync logic here
  console.log('Syncing health data after being offline');
}
