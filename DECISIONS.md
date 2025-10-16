# Technical Decisions

## Open-Source Model Selection

### TTS (Text-to-Speech)
**Selected: gTTS (Google Text-to-Speech)**

**Rationale:**
- High-quality speech synthesis with natural-sounding voices
- Easy integration with FastAPI and WebSocket streaming
- Minimal dependencies and setup complexity
- Works reliably in Docker containers
- Good performance for demonstration purposes

**Migration from pyttsx3:**
- **Original choice**: pyttsx3 with espeak backend was initially selected for offline use
- **Problem encountered**: pyttsx3 had issues in Docker environment without sound system
- **Solution**: Switched to gTTS for reliable speech synthesis
- **Trade-off**: Now requires internet connection but provides better quality

**Alternatives considered:**
- **pyttsx3 + espeak**: Good for offline use but problematic in Docker
- **Tacotron2/NeMo**: Too heavy for CPU-only inference, requires GPU
- **Coqui TTS**: More complex setup, better suited for production with GPU

### ASR (Automatic Speech Recognition)
**Selected: OpenAI Whisper (base.en)**

**Rationale:**
- State-of-the-art accuracy for English speech recognition
- Good performance on CPU (though slower than GPU)
- Excellent handling of various audio formats and quality
- Built-in support for audio preprocessing and normalization
- Well-documented API and easy integration

**Alternatives considered:**
- **DeepSpeech**: Older model, lower accuracy
- **Wav2Vec2**: More complex setup, requires fine-tuning for optimal results
- **AssemblyAI/Rev.ai**: Cloud-based, requires internet and API keys

## Architecture Decisions

### Microservices Architecture
**Decision: Separate containers for TTS, ASR, and Gateway**

**Benefits:**
- Independent scaling and deployment
- Technology isolation (different ML frameworks)
- Clear separation of concerns
- Easier testing and debugging
- Fault isolation

### Communication Protocols
**TTS Service:**
- WebSocket for real-time streaming (`ws://tts:8082/ws/tts`)
- HTTP POST for simple requests (`POST /api/tts`)

**ASR Service:**
- HTTP POST for file-based processing (`POST /api/stt/bytes`)

**Gateway:**
- WebSocket proxy for TTS (`ws://gateway:8000/ws/tts`)
- HTTP echo endpoint (`POST /api/echo-bytes`)

### Audio Format
**Decision: 16-bit PCM, mono, configurable sample rates**

**Rationale:**
- Standard format supported by all audio libraries
- Efficient for streaming (no compression overhead)
- Easy to process and convert
- Compatible with most speech processing models

## Implementation Details

### Streaming Implementation
**TTS Streaming:**
- Fixed chunk size (1024 bytes by default)
- Real-time streaming without buffering entire audio
- Proper stream finalization with end markers
- Error handling for stream interruptions

**Audio Processing:**
- Automatic resampling to target sample rates
- Stereo to mono conversion when needed
- Audio normalization for consistent levels
- Proper PCM format conversion

### Error Handling
- Structured logging with JSON format
- Comprehensive exception handling
- Graceful degradation for service failures
- Clear error messages for API consumers

### Configuration Management
- Environment-based configuration
- Separate settings for each service
- Docker-friendly configuration
- Health check endpoints for monitoring

## Challenges and Solutions

### Challenge 1: CPU Performance
**Problem:** Whisper model is slow on CPU
**Solution:** 
- Used whisper-base.en (smaller model)
- Optimized audio preprocessing
- Acceptable for demonstration purposes
- Added timeout handling for long audio

### Challenge 2: Audio Format Compatibility
**Problem:** Different audio formats and sample rates
**Solution:**
- Implemented robust audio preprocessing pipeline
- Automatic format detection and conversion
- Support for various input formats
- Standardized PCM output

### Challenge 3: Streaming Reliability
**Problem:** WebSocket connections can be unstable
**Solution:**
- Implemented connection management
- Proper error handling and reconnection logic
- Stream finalization markers
- Timeout handling

## What Didn't Work Out of the Box

### TTS Engine Initialization
- **Issue:** pyttsx3 had issues in Docker environment without sound system
- **Solution:** Switched to gTTS which works reliably in containers
- **Implementation:** Added ffmpeg to Dockerfile for gTTS audio processing

### Whisper Model Download
- **Issue:** Model download can be slow on first run
- **Solution:** Pre-download models in Docker build or use volume mounting
- **Note:** In production, models should be pre-cached

### Audio Format Handling
- **Issue:** Various audio formats require different processing
- **Solution:** Implemented comprehensive audio preprocessing pipeline
- **Enhancement:** Could add more format support (MP3, AAC, etc.)

## Future Improvements (TODO/Roadmap)

### Performance Optimizations
- [ ] GPU support for faster Whisper inference
- [ ] Model quantization for reduced memory usage
- [ ] Caching for frequently requested TTS
- [ ] Batch processing for multiple audio files

### Feature Enhancements
- [ ] Multiple language support
- [ ] Voice customization options
- [ ] Audio format conversion endpoints
- [ ] Real-time audio streaming from microphone

### Production Readiness
- [ ] Comprehensive unit and integration tests
- [ ] Performance monitoring and metrics
- [ ] Load balancing and scaling
- [ ] Security enhancements (authentication, rate limiting)

### DevOps Improvements
- [ ] Kubernetes deployment manifests
- [ ] CI/CD pipeline
- [ ] Automated testing
- [ ] Monitoring and alerting

## Resource Requirements

### CPU Requirements
- **Minimum:** 2 cores, 4GB RAM
- **Recommended:** 4 cores, 8GB RAM
- **For production:** 8+ cores, 16GB+ RAM

### Storage Requirements
- **Models:** ~500MB for whisper base.en
- **Logs:** Variable based on usage
- **Audio cache:** Optional, depends on caching strategy

### Network Requirements
- **Internal:** Low latency between services
- **External:** Depends on client usage patterns
- **Bandwidth:** Audio streaming requires stable connection
