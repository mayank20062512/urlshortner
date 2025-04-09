# urlshortner
this is an url shortner made using Flask

Features of this app
Core Functionality:
Core URL Shortening: Accepts long URLs and generates a unique, shorter alias (short code).
Short URL Redirection: When the short URL is accessed, it redirects the user to the original long URL.
Database Persistence (Firebase Firestore): Stores the mapping between short codes and long URLs, along with other data, in a cloud-based NoSQL database (Firestore), ensuring data persists between application restarts.
Click Tracking: Counts the number of times each short URL is accessed/clicked. (Stored in Firestore).
User Experience (UI/UX):
Modern User Interface: Clean layout with improved styling using CSS.
Light/Dark Mode Toggle: Allows users to switch between light and dark themes for visual preference.
Theme Preference Saving: Remembers the user's selected theme (light/dark) using browser localStorage, so it persists across sessions.
Responsive Design: The interface adapts reasonably well to different screen sizes (desktops, tablets, mobiles).
User Feedback (Flash Messages): Provides clear messages to the user for success (e.g., URL shortened), errors (e.g., invalid URL), or information (e.g., URL already exists).
Utility Features:
QR Code Generation: Automatically generates a downloadable QR code for each successfully shortened URL, making it easy to share visually or on mobile devices.
Duplicate URL Prevention: Checks if a long URL has already been shortened and returns the existing short code instead of creating a new one.
User-Specific Features (Basic Implementation):
Basic Client-Side User Identification: Generates and stores a simple unique ID in the browser's localStorage to associate links with a specific user/browser session (Note: Not secure authentication).
User-Specific Link History (Last 10): Displays the last 10 URLs shortened by the current user (based on the localStorage ID).
History Item Deletion: Allows the user to remove individual links from their displayed history.
Technical/Backend Features:
Backend API for History Management: Includes specific API endpoints (/api/history/...) for fetching and deleting user history data, demonstrating separation of concerns.
Firebase Admin SDK Integration: Uses the official Python SDK to interact securely with Firebase Firestore from the backend.
Atomic Click Increment: Uses Firestore's atomic increment operation for safer and more accurate click counting, especially under potential concurrent access.
