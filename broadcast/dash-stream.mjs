import puppeteer from "puppeteer-core";
import http from "http";
const W=672, H=1080, FPS=2, URL="http://localhost:1880/ui/";
const browser = await puppeteer.launch({executablePath:"/usr/bin/chromium", headless:"new",
  args:["--no-sandbox","--disable-gpu","--disable-dev-shm-usage","--disable-software-rasterizer","--force-device-scale-factor=1"]});
const page = await browser.newPage();
await page.setViewport({width:W,height:H,deviceScaleFactor:1});
await page.goto(URL,{waitUntil:"networkidle2",timeout:60000});
await new Promise(r=>setTimeout(r,3000));
let latest = await page.screenshot({type:"jpeg",quality:80});
setInterval(async()=>{ try{ latest=await page.screenshot({type:"jpeg",quality:80}); }catch(e){} }, Math.round(1000/FPS));
http.createServer((req,res)=>{
  res.writeHead(200,{"Content-Type":"multipart/x-mixed-replace; boundary=frame","Cache-Control":"no-cache"});
  let alive=true; req.on("close",()=>alive=false);
  const tick=()=>{ if(!alive)return; res.write(`--frame\r\nContent-Type: image/jpeg\r\nContent-Length: ${latest.length}\r\n\r\n`); res.write(latest); res.write("\r\n"); setTimeout(tick,Math.round(1000/FPS)); };
  tick();
}).listen(8090,"127.0.0.1",()=>console.log("dash mjpeg on :8090"));
