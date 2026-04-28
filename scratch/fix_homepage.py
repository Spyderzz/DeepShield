import sys
import io

path = 'c:/Users/athar/Desktop/minor2/frontend/src/pages/HomePage.jsx'
with io.open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Route video properly
old_run_analysis = """    try {
      const data = await analyzeImage(file);
      setProgress(100);"""
new_run_analysis = """    try {
      let data;
      if (file.type && file.type.startsWith('video/')) {
        const { submitVideoJob, pollVideoJob } = await import('../services/analyzeApi.js');
        const job = await submitVideoJob(file, { cache: true });
        data = await pollVideoJob(job.job_id || job.id, { onProgress: (j) => setProgress(j.progress || 50) });
      } else {
        data = await analyzeImage(file);
      }
      setProgress(100);"""
content = content.replace(old_run_analysis, new_run_analysis)

# Fix 2: Accept video file input
old_input = """                  <input
                    ref={fileRef}
                    type="file"
                    accept="image/*"
                    style={{ display: 'none' }}"""
new_input = """                  <input
                    ref={fileRef}
                    type="file"
                    accept="image/*,video/*"
                    style={{ display: 'none' }}"""
content = content.replace(old_input, new_input)

# Fix 3: Invert fakeScore logic
old_score = """  const fakeProb = verdict.fake_probability ?? expl.fake_probability ?? verdict.confidence ?? 0.5;
  const score = typeof verdict.authenticity_score === 'number'
    ? Math.round(verdict.authenticity_score)
    : Math.round(Math.max(0, Math.min(1, 1 - fakeProb)) * 100);
  const verdictColor = score > 65 ? 'safe' : score > 40 ? 'warn' : 'danger';
  const verdictLabel = (verdict.label || verdict.classification || (score < 40 ? 'LIKELY FAKE' : score < 65 ? 'SUSPICIOUS' : 'LIKELY REAL')).toString().toUpperCase();"""

new_score = """  const fakeProb = verdict.fake_probability ?? expl.fake_probability ?? verdict.confidence ?? 0.5;
  const authScore = typeof verdict.authenticity_score === 'number'
    ? Math.round(verdict.authenticity_score)
    : Math.round(Math.max(0, Math.min(1, 1 - fakeProb)) * 100);
  const score = 100 - authScore; // Display as deepfake probability
  const verdictColor = score <= 35 ? 'safe' : score <= 60 ? 'warn' : 'danger';
  const verdictLabel = (verdict.label || verdict.classification || (score <= 35 ? 'LIKELY REAL' : score <= 60 ? 'SUSPICIOUS' : 'LIKELY FAKE')).toString().toUpperCase();"""
content = content.replace(old_score, new_score)

# Fix 4: Label Deepfake Probability
content = content.replace('<span className="eyebrow">Authenticity verdict</span>', '<span className="eyebrow">Deepfake probability</span>')

# Fix 5: Handle video HTML playback
old_heatmap = """          <div className="heatmap-stage">
            <img src={imgUrl} alt="" className="heatmap-base" />"""
new_heatmap = """          <div className="heatmap-stage">
            {result.media_type === 'video' ? (
              <video src={imgUrl} controls className="heatmap-base" style={{ maxHeight: 520, objectFit: 'contain', width: '100%' }} />
            ) : (
              <img src={imgUrl} alt="" className="heatmap-base" />
            )}"""
content = content.replace(old_heatmap, new_heatmap)

# Fix 6: hide heatmap controls for video
old_heatmap_seg = """{heatmapMode === 'heatmap' && ("""
new_heatmap_seg = """{heatmapMode === 'heatmap' && result.media_type !== 'video' && ("""
content = content.replace(old_heatmap_seg, new_heatmap_seg)

old_ela_seg = """{heatmapMode === 'ela' && ("""
new_ela_seg = """{heatmapMode === 'ela' && result.media_type !== 'video' && ("""
content = content.replace(old_ela_seg, new_ela_seg)

old_boxes_seg = """{heatmapMode === 'boxes' && ("""
new_boxes_seg = """{heatmapMode === 'boxes' && result.media_type !== 'video' && ("""
content = content.replace(old_boxes_seg, new_boxes_seg)


with io.open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("done")
