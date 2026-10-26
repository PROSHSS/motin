import {existsSync} from 'node:fs';
import {Config} from '@remotion/cli/config';

// Reutiliza o Chromium do ambiente; em outros sistemas, mantém o padrão do Remotion.
const browser = process.env.REMOTION_BROWSER_EXECUTABLE ?? '/usr/bin/chromium';
if (existsSync(browser)) Config.setBrowserExecutable(browser);
Config.setVideoImageFormat('jpeg');
Config.setPixelFormat('yuv420p');
