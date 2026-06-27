import 'package:just_audio/just_audio.dart';
import 'package:just_audio_background/just_audio_background.dart';
import 'package:youtube_explode_dart/youtube_explode_dart.dart';

/// Buddy's in-app music player. Plays the audio of a YouTube video (resolved to a streamable
/// URL) through just_audio, with background playback + lock-screen / notification controls
/// provided by just_audio_background. A single shared instance app-wide.
class BuddyPlayer {
  BuddyPlayer._();
  static final BuddyPlayer instance = BuddyPlayer._();

  final AudioPlayer player = AudioPlayer();
  final YoutubeExplode _yt = YoutubeExplode();
  String? nowPlaying;

  Stream<bool> get playingStream => player.playingStream;
  bool get isPlaying => player.playing;

  /// Resolve [videoId] to an audio stream and start playback (shows lock-screen controls).
  Future<void> playYouTube(String videoId, {String title = 'Now Playing'}) async {
    nowPlaying = title;
    final manifest = await _yt.videos.streamsClient.getManifest(videoId);
    final audio = manifest.audioOnly.withHighestBitrate();
    await player.setAudioSource(AudioSource.uri(
      Uri.parse(audio.url.toString()),
      tag: MediaItem(id: videoId, title: title, artist: 'Buddy'),
    ));
    await player.play();
  }

  /// Play a direct audio/file URL (e.g. a local or downloaded track).
  Future<void> playUrl(String url, {String title = 'Now Playing'}) async {
    nowPlaying = title;
    await player.setAudioSource(AudioSource.uri(
      Uri.parse(url),
      tag: MediaItem(id: url, title: title, artist: 'Buddy'),
    ));
    await player.play();
  }

  Future<void> toggle() => player.playing ? player.pause() : player.play();
  Future<void> stop() async {
    nowPlaying = null;
    await player.stop();
  }
}
