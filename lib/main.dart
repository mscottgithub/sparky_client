import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sparky_client/screens/home_screen.dart';
import 'package:sparky_client/providers/theme_provider.dart';
import 'package:sparky_client/app_colors.dart';

void main() {
  runApp(
    const ProviderScope(
      child: SparkyApp(),
    ),
  );
}

/// Root application widget with Riverpod ProviderScope
class SparkyApp extends ConsumerWidget {
  const SparkyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Theme mode - keeping provider for future use, but forcing light mode for now
    final _ = ref.watch(themeModeProvider);

    return MaterialApp(
      title: 'Sparky Voice AI',
      theme: _buildLightTheme(),
      darkTheme: _buildDarkTheme(),
      themeMode: ThemeMode.light, // FORCE LIGHT MODE - ignore provider for now
      home: const HomeScreen(), // Back to home screen
    );
  }

  ThemeData _buildLightTheme() {
    // Use AppColors constants for consistency
    // Final colors: Powder Blue #8BBCC2, Thistle #977597, Pale Green #78C778
    const powderBlue = AppColors.powderBlue; // Powder Blue #8BBCC2
    const thistle = AppColors.thistle; // Thistle #977597
    
    // DEBUG: Print colors to verify they're being built
    debugPrint('🎨 Building theme with Powder Blue: #8BBCC2, Thistle: #977597, Pale Green: #78C778');

    // DISABLE Material 3 completely - it was overriding everything!
    // Use Material 2 for reliable color control
    final customColorScheme = ColorScheme.light(
      primary: thistle,
      secondary: thistle,
      surface: powderBlue,
      background: powderBlue,
      error: Colors.red,
      onPrimary: Colors.black,
      onSecondary: Colors.black,
      onSurface: Colors.black87,
      onBackground: Colors.black87,
      onError: Colors.white,
    );

    return ThemeData(
      // DISABLE Material 3 - use Material 2 which respects scaffoldBackgroundColor
      useMaterial3: false,
      colorScheme: customColorScheme,
      scaffoldBackgroundColor: powderBlue, // Powder Blue background - exact color
      appBarTheme: AppBarTheme(
        backgroundColor: thistle, // Thistle for AppBar - exact color
        foregroundColor: Colors.purple.shade900,
        systemOverlayStyle: SystemUiOverlayStyle.dark, // Ensure visibility
        elevation: 0, // Remove elevation that affects color
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: thistle, // Thistle for text input - exact color
        border: const OutlineInputBorder(),
      ),
      cardTheme: CardThemeData(
        color: const Color(0xFF78C778), // Pale Green #78C778 for cards
        elevation: 0,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF78C778), // Pale Green #78C778
          elevation: 0,
        ),
      ),
    );
  }

  ThemeData _buildDarkTheme() {
    return ThemeData(
      colorScheme: ColorScheme.fromSeed(
        seedColor: Colors.blue,
        brightness: Brightness.dark,
      ),
      useMaterial3: true,
      scaffoldBackgroundColor: Colors.grey.shade900,
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.grey.shade800,
        foregroundColor: Colors.white,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.grey.shade800,
        border: const OutlineInputBorder(),
      ),
    );
  }
}
