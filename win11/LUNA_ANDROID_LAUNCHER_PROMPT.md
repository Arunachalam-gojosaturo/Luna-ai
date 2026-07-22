# LUNA OS: Android Jarvis Launcher Prompt
## Master Instruction Prompt for Google AI (Gemini)

Copy and paste the prompt below into Google AI (Gemini) to generate the complete Android Launcher codebase.

---

### 📋 COPY THE PROMPT BELOW:

```markdown
You are an expert Android developer and UI/UX designer. I need you to generate a fully functional **Android Launcher** (Home Screen Replacement) written in **Kotlin** with **Jetpack Compose**. 

This is NOT a regular Android app. It is a Home replacement app that handles the HOME button press, replaces the standard phone launcher, and runs a terminal-like console interface inspired by Iron Man's Jarvis / Aris UI, integrated with LUNA AI (my personal desktop AI assistant).

Follow the instructions below to generate the complete structure, configuration files, and code.

---

### 1. Key Requirements for an Android Launcher (Why standard LLM generations fail)
To ensure Android recognizes this as a Launcher and not a standard app, you MUST implement these configuration points:

1. **AndroidManifest.xml intent-filter**: The launcher activity MUST have the following intent-filter to register with the Android OS as a Home replacement:
   ```xml
   <intent-filter>
       <action android:name="android.intent.action.MAIN" />
       <category android:name="android.intent.category.HOME" />
       <category android:name="android.intent.category.DEFAULT" />
   </intent-filter>
   ```

2. **Package Visibility Permissions (Android 11 / API 30+)**: To query installed apps and list them, you must include the `<queries>` element or request `QUERY_ALL_PACKAGES` in the manifest. Use:
   ```xml
   <uses-permission android:name="android.permission.QUERY_ALL_PACKAGES" />
   ```

3. **Core Permissions**:
   - `android.permission.CAMERA` (for the flashlight toggle command)
   - `android.permission.ACCESS_FINE_LOCATION` / `ACCESS_COARSE_LOCATION` (for locateme command)
   - `android.permission.CALL_PHONE` (for phone calls command)
   - `android.permission.CHANGE_WIFI_STATE` / `CHANGE_NETWORK_STATE` / `UPDATE_DEVICE_STATS` (for wifi toggling)
   - `android.permission.BLUETOOTH` / `android.permission.BLUETOOTH_ADMIN` / `android.permission.BLUETOOTH_CONNECT` (for bluetooth toggling)

---

### 2. UI/UX Design: Jarvis Terminal Console
- **Background**: High-tech sci-fi theme. Smooth dark gradient background (pure black/dark cyan) with optional glowing holographic matrices or particles.
- **Top Bar / Status Bar**: Custom status indicators showing device vitals (CPU load, RAM usage, storage space, battery percentage, active wireless networks) updated in real-time.
- **Main Output Area**: A scrolling console terminal. It should render stdout-like messages, system logs, notifications, and results of executed commands. Features animated green/cyan monospaced text.
- **Bottom Command Input**: A persistent CLI input text field with a leading `luna > ` or `jarvis > ` prompt. Typing anything performs fuzzy search against installed apps to launch them, or interprets specific terminal commands.
- **Hacker Lock Screen**: An optional fullscreen overlay displaying scrolling terminal logs, system stats, and a custom keypad code input to "unlock" the launcher.

---

### 3. CLI Command Specifications
Implement a command processing engine in Kotlin that handles the following inputs in the console:

- `uninstall <app_name>`: Launches the system uninstallation intent for the matched app.
- `info <app_name>`: Opens the application details page in Android Settings for the matched app.
- `add <app_name> <folder_name>`: Groups apps into folders (stored locally in room database/shared preferences).
- `remove <app_name> <folder_name>`: Removes an app from a folder.
- `hide <app/contact>`: Disables the app/contact from showing in the main search list.
- `show <app/contact>`: Re-enables the hidden app/contact.
- `folder <folder_name>`: Lists the contents of the specified folder.
- `apps`: Displays the list of all installed apps in a clean, scrollable terminal table.
- `clipboard`: Retrieves and displays the current text in the system clipboard.
- `restart`: Restarts the launcher process/activity.
- `clear`: Clears the console output history.
- `wifi`: Toggles WiFi state (or launches system WiFi settings if direct toggle is blocked by Android API restrictions).
- `bluetooth`: Toggles Bluetooth (or opens Bluetooth settings panel).
- `flash`: Toggles the device flashlight.
- `weather`: Queries a weather API or returns mock weather info.
- `shell <command>`: Simulates a local shell terminal execution.
- `locateme`: Shows current location coordinates and attempts to load a static map/satellite visualization.
- `note <note_content>`: Saves notes to a local note database.
- `encrypt <message>`: Encrypts the message using standard crypt-algorithms (e.g. AES or Caesar) and displays the result.
- `ls <app_name>`: Prints version, package name, installation date, and storage size of the application.
- `code`: Initiates a fullscreen animation of scrolling Matrix-like green hacker code.
- `number <phone_number>`: Directly dials/makes a phone call to the number.
- `equation <expression>`: Parses and calculates mathematical equations (e.g., `12 * (5 + 7)`).
- `<app_name>` (fallback): If the user types any name that matches an installed app, launch the app directly.

---

### 4. Integration with LUNA AI & Google AI (Gemini)
To make this launcher smart, integrate two AI components:

1. **Google AI SDK Integration (Local Core)**:
   - Implement the Google GenAI SDK (`com.google.android.play:core-common` or `com.google.ai.client.generativeai:generativeai`) to process conversational inputs.
   - When users prefix inputs with `luna` or `jarvis` (e.g., `luna how many miles to the moon?`), route the query to Gemini (`gemini-2.5-flash`) using a client-side API key.
   
2. **Luna Desktop Server Sync (Local Web Client)**:
   - Add a configuration screen to input the IP address of the LUNA desktop server (FastAPI running on port 3000).
   - If configured, forward CLI inputs to the desktop API: `POST http://<desktop-ip>:3000/api/luna/execute`.
   - Read the JSON response and map LUNA's system commands (like media controls, system status, web scraping outputs) directly on the phone or sync execution back to the PC.

---

### 5. Codebase Generation Scope
Please provide:
1. `build.gradle.kts` (app level) with Compose, GenAI, and system utility dependencies.
2. `AndroidManifest.xml` with complete Launcher intent filters and package querying permissions.
3. `MainActivity.kt` - The entry point containing the Compose UI (scrolling terminal log, CLI input text field, and status indicators) and system lifecycle management.
4. `CommandProcessor.kt` - The Kotlin parser that routes all CLI commands (`wifi`, `flash`, `uninstall`, `info`, etc.) to their native Android APIs.
5. `AppRepository.kt` - Class utilizing `PackageManager` to retrieve, filter, and launch applications.
```

---

## 🛠️ Why Your Previous Code Failed to Register as a Launcher

When asking LLMs to create an Android App, they default to writing a standard activity. Here is why the Launcher wasn't detected by Android as a Home Replacement:

1. **Missing Intent Filter Categories**:
   Standard apps only have:
   ```xml
   <category android:name="android.intent.category.LAUNCHER" />
   ```
   But a Launcher/Home replacement MUST have:
   ```xml
   <category android:name="android.intent.category.HOME" />
   <category android:name="android.intent.category.DEFAULT" />
   ```
   Without these two categories under `android.intent.action.MAIN`, clicking your phone's Home button will never prompt you to select your app as the default Home Screen.

2. **Package visibility restrictions (Android 11+)**:
   Starting in Android 11, apps cannot see other installed apps by default. A launcher that tries to query packages will return an empty list unless `<uses-permission android:name="android.permission.QUERY_ALL_PACKAGES" />` is declared, or a `<queries>` block is added to `AndroidManifest.xml`.

3. **Overlay & Draw Permissions**:
   Commands like "Hacker lock screen" require permission to draw over other apps (`android.permission.SYSTEM_ALERT_WINDOW`) if you want it to act as an overlay or custom lock screen.

---

## 📱 Architecture Diagram: Luna Jarvis Launcher

```mermaid
graph TD
    User([User Input]) -->|CLI Text or Voice| UI[Jetpack Compose Terminal UI]
    UI -->|Evaluate Command| CmdProc[CommandProcessor.kt]
    
    CmdProc -->|Local Command: wifi, flash, app launch| OS[Android OS APIs]
    CmdProc -->|App Management: uninstall, info, ls| PackMgr[PackageManager Client]
    CmdProc -->|AI Conversation: "luna ..."| GeminiSDK[Google AI SDK - Gemini 2.5]
    CmdProc -->|Sync Command: "desktop ..."| LunaAPI[LUNA FastAPI Client]
    
    LunaAPI -->|POST /api/luna/execute| DesktopServer[LUNA Desktop Server - Port 3000]
    DesktopServer -->|Control PC| LinuxOS[Arch Linux Workstation]
    
    OS -->|Output/Vitals| UI
    PackMgr -->|App List / Icons| UI
    GeminiSDK -->|Text Response| UI
    LunaAPI -->|JSON Actions/Speech| UI
```

---

## 🚀 Step-by-Step Implementation Guide

Follow these steps to build the Android Launcher project generated by Gemini:

### Step 1: Create a new Android Project
1. Open Android Studio.
2. Select **New Project** -> **Empty Compose Activity**.
3. Name it `LunaJarvisLauncher`, set Package Name to `com.luna.jarvis.launcher`, and set Min SDK to **26** (Android 8.0) or higher.

### Step 2: Configure AndroidManifest.xml
Replace your `app/src/main/AndroidManifest.xml` with the configuration generated. Ensure the `<activity>` tag looks like this:
```xml
<activity
    android:name=".MainActivity"
    android:exported="true"
    android:launchMode="singleInstance"
    android:stateNotNeeded="true"
    android:theme="@style/Theme.LunaJarvisLauncher">
    <intent-filter>
        <action android:name="android.intent.action.MAIN" />
        <category android:name="android.intent.category.HOME" />
        <category android:name="android.intent.category.DEFAULT" />
    </intent-filter>
</activity>
```

### Step 3: Implement Gradle Configuration
Add the dependency for Google GenAI in your `app/build.gradle.kts`:
```kotlin
dependencies {
    // Jetpack Compose
    implementation("androidx.compose.ui:ui:1.6.0")
    implementation("androidx.compose.material3:material3:1.2.0")
    
    // Google AI Client for Gemini
    implementation("com.google.ai.client.generativeai:generativeai:0.7.0")
    
    // Coroutines & Lifecycle
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.7.0")
}
```

### Step 4: Run & Register as Default Launcher
1. Connect your Android phone via USB and enable USB Debugging.
2. Build and run the app from Android Studio.
3. Once installed, press the **Home button** on your phone.
4. Android will display a prompt asking you to **"Select a Home app"**.
5. Choose **Luna Jarvis Launcher** and select **"Always"**.
6. Type `apps` in the console input to see all your applications, or type `luna hello` to test the AI.
