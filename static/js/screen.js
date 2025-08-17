/*
Copyright (C) 2021  Qijun Gu
Modified to add Audio playback

This file is part of Screenshare.

Screenshare is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Screenshare is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Screenshare. If not, see <https://www.gnu.org/licenses/>.
*/

var frameinterval = 200;     // 200 ms → 5 fps
var frameerrcount = 0;
var screenfeedtimeout = null;

var audioplaying = false;
var audioCtx = null;
var audiofeedinterval = 100; // poll every 100 ms

$(function() {
	screenfeed();

	// Start audio only after user interaction
	$(document).on("click", function() {
		if (!audioplaying) {
			audioplaying = true;
			startAudioFeed();
		}
	});
});

function screenfeed() {
	if (frameerrcount < 0) return;
	$.post('../screenfeed/')
	.then(function(r){
		var ret = $.parseJSON(r);
		$('img.livescreen').attr('src', 'data:image/jpeg;base64,'+ret[1]);
		frameerrcount = 0;
		screenfeedtimeout = setTimeout(screenfeed, frameinterval)
	}, function(r) {
		if (frameerrcount < 0) return;
		frameerrcount++;
		screenfeedtimeout = setTimeout(screenfeed, frameinterval)
		if (frameerrcount > 20) {
			clearTimeout(screenfeedtimeout);
			frameerrcount = -1;
			$.alert({
			    title: 'Error!',
			    content: 'Lost screen from server. Refresh this page later...'
			});
		}
	});
}

// ====== Audio Feed ======
function startAudioFeed() {
	if (!audioCtx) {
		audioCtx = new (window.AudioContext || window.webkitAudioContext)();
	}
	audiofeed();
}

function audiofeed() {
	$.post('../audiofeed/')
	.then(function(r){
		var ret = $.parseJSON(r);
		if (ret[0]) {
			var base64 = ret[1];
			var raw = atob(base64);
			var buffer = new ArrayBuffer(raw.length);
			var view = new Uint8Array(buffer);
			for (var i = 0; i < raw.length; i++) {
				view[i] = raw.charCodeAt(i);
			}

			// PCM16LE stereo 44100Hz
			var numChannels = 2;
			var sampleRate = 44100;
			var frameCount = view.length / 2 / numChannels;
			var audioBuffer = audioCtx.createBuffer(numChannels, frameCount, sampleRate);

			for (var ch = 0; ch < numChannels; ch++) {
				var channelData = audioBuffer.getChannelData(ch);
				for (var i = 0; i < frameCount; i++) {
					var idx = (i * numChannels + ch) * 2;
					var sample = (view[idx] | (view[idx+1] << 8));
					if (sample >= 32768) sample -= 65536;
					channelData[i] = sample / 32768.0;
				}
			}

			var source = audioCtx.createBufferSource();
			source.buffer = audioBuffer;
			source.connect(audioCtx.destination);
			source.start();
		}
		setTimeout(audiofeed, audiofeedinterval);
	}, function(r) {
		// retry on error
		setTimeout(audiofeed, audiofeedinterval);
	});
}
