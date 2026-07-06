# BotaAld Android App

Полнофункциональное Android приложение, готовое к сборке APK.

## Требования
- Android SDK 34
- Kotlin 1.9.0
- Gradle 8.1.0
- Java 11+

## Сборка APK

### Debug версия:
```bash
./gradlew assembleDebug
```
APK будет создан в: `app/build/outputs/apk/debug/app-debug.apk`

### Release версия:
```bash
./gradlew assembleRelease
```
APK будет создан в: `app/build/outputs/apk/release/app-release.apk`

## Возможности
- Минимальная версия Android: 7.0 (API 24)
- Целевая версия Android: 14.0 (API 34)
- Поддержка Kotlin
- Material Design 3
- Binding для View

## Установка
```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```
