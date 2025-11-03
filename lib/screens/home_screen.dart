import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sparky_client/screens/chat_screen.dart';
import 'package:sparky_client/screens/audio_test_screen.dart';
import 'package:sparky_client/screens/voice_screen.dart';
import 'package:sparky_client/providers/theme_provider.dart';
import 'package:sparky_client/app_colors.dart';

/// Main home screen for Sparky Client
/// Navigation hub for chat and audio test screens
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeModeProvider);

    return ColoredBox(
      color: AppColors.powderBlue, // Powder Blue #8BBCC2
      child: Scaffold(
        backgroundColor: Colors.transparent, // Let ColoredBox color show through
        extendBodyBehindAppBar: false,
        appBar: PreferredSize(
          preferredSize: const Size.fromHeight(kToolbarHeight),
          child: ColoredBox(
            color: AppColors.thistle, // Thistle #977597
            child: AppBar(
              title: const Text('Sparky Client'),
              backgroundColor: Colors.transparent, // Transparent so ColoredBox shows
              foregroundColor: Colors.purple.shade900,
              elevation: 0, // Remove shadow
              actions: [
                IconButton(
                  icon: Icon(
                    themeMode == ThemeMode.dark ? Icons.light_mode : Icons.dark_mode,
                  ),
                  onPressed: () {
                    ref.read(themeModeProvider.notifier).toggleTheme();
                  },
                  tooltip: themeMode == ThemeMode.dark ? 'Switch to Light Mode' : 'Switch to Dark Mode',
                ),
              ],
            ),
          ),
        ),
        body: Center(
          child: SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: ColoredBox(
                color: AppColors.paleGreen, // Pale Green #78C778
                child: Container(
                  padding: const EdgeInsets.all(32.0),
                  decoration: BoxDecoration(
                    color: AppColors.paleGreen, // Pale Green #78C778 background
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                    const Icon(
                      Icons.mic,
                      size: 80,
                      color: Colors.blue,
                    ),
                    const SizedBox(height: 24),
                    const Text(
                      'Sparky Voice AI',
                      style: TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Week 2 - Day 4: Audio Recording',
                      style: TextStyle(
                        fontSize: 16,
                        color: Colors.grey,
                      ),
                    ),
                    const SizedBox(height: 48),
                    SizedBox(
                      width: 250,
                      child: ElevatedButton.icon(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => const ChatScreen(),
                            ),
                          );
                        },
                        icon: const Icon(Icons.chat),
                        label: const Text('Text Chat'),
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          textStyle: const TextStyle(fontSize: 18),
                          backgroundColor: AppColors.paleGreen, // Pale Green #78C778
                          foregroundColor: Colors.green.shade900,
                          elevation: 0, // Remove Material elevation shadow
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    SizedBox(
                      width: 250,
                      child: ElevatedButton.icon(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => const VoiceScreen(),
                            ),
                          );
                        },
                        icon: const Icon(Icons.mic),
                        label: const Text('Voice Chat'),
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          textStyle: const TextStyle(fontSize: 18),
                          backgroundColor: AppColors.paleGreen, // Pale Green #78C778
                          foregroundColor: Colors.green.shade900,
                          elevation: 0, // Remove Material elevation shadow
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    SizedBox(
                      width: 250,
                      child: ElevatedButton.icon(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => const AudioTestScreen(),
                            ),
                          );
                        },
                        icon: const Icon(Icons.graphic_eq),
                        label: const Text('Audio Latency Test'),
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          textStyle: const TextStyle(fontSize: 18),
                          backgroundColor: AppColors.paleGreen, // Pale Green #78C778
                          foregroundColor: Colors.green.shade900,
                          elevation: 0, // Remove Material elevation shadow
                        ),
                      ),
                    ),
                    const SizedBox(height: 32),
                    Card(
                      color: AppColors.paleGreen, // Pale Green #78C778
                      elevation: 0, // Remove Material elevation shadow
                      child: const Padding(
                        padding: EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Features:',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 16,
                              ),
                            ),
                            SizedBox(height: 8),
                            Text('• Text chat with Sparky AI'),
                            Text('• Voice chat with audio recording'),
                            Text('• Real-time message streaming'),
                            Text('• Desktop UX (right-click, shortcuts)'),
                            Text('• Audio latency validation'),
                          ],
                        ),
                      ),
                    ),
                  ],
                ), // Close Column
              ), // Close Container
            ), // Close inner ColoredBox
          ), // Close Padding
        ), // Close SingleChildScrollView
      ), // Close Center
    ), // Close Scaffold
    ); // Close outer ColoredBox
  }
}