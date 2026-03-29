import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";

export async function POST(request: NextRequest) {
  try {
    const { url, platform = "meta", mock, mockCategory } = await request.json();

    if (!url && !mock) {
      return NextResponse.json({ error: "Missing URL" }, { status: 400 });
    }

    // Call Python backend
    const result = await new Promise((resolve, reject) => {
      const scriptPath = path.join(process.cwd(), "..", "api_backend.py");
      const productUrl = mock ? "mock" : url;
      const args = [scriptPath, productUrl, platform];
      if (mock && mockCategory) args.push(mockCategory);

      const pythonProcess = spawn("python3", args, {
        cwd: path.join(process.cwd(), ".."),
      });

      let stdout = "";
      let stderr = "";

      pythonProcess.stdout.on("data", (data) => {
        stdout += data.toString();
      });

      pythonProcess.stderr.on("data", (data) => {
        stderr += data.toString();
      });

      pythonProcess.on("close", (code) => {
        if (code === 0) {
          try {
            resolve(JSON.parse(stdout));
          } catch {
            reject(new Error(`JSON parse error: ${stdout}`));
          }
        } else {
          reject(new Error(`Python exited with code ${code}: ${stderr}`));
        }
      });

      pythonProcess.on("error", (err) => {
        reject(err);
      });
    });

    return NextResponse.json(result);
  } catch (error) {
    console.error("API error:", error);
    return NextResponse.json(
      { error: "Internal server error", detail: String(error) },
      { status: 500 }
    );
  }
}
