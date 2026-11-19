using GBX.NET;
using GBX.NET.Engines.Plug;
using System.Text.Json;
using System.Text.Json.Serialization;
using TM_GenericMapping.Items.GbxConversion;

public class ReadPakAssetsPayload
{
    /// <summary>GameData folder of a pak extract (contains Stadium/, Techno3/, ...).</summary>
    public string Root { get; set; } = "";
    /// <summary>Where the result json is written.</summary>
    public string OutputPath { get; set; } = "";
}

public class PakBitmap
{
    /// <summary>Path relative to Root, forward slashes.</summary>
    public string Path { get; set; } = "";
    /// <summary>Referenced image relative to Root (null if the bitmap has no file reference).</summary>
    public string? Image { get; set; }
    public BitmapConfig? Config { get; set; }
    public string? Error { get; set; }
}

public class PakRefs
{
    public string Path { get; set; } = "";
    /// <summary>External files relative to Root.</summary>
    public List<string> Refs { get; set; } = [];
    public string? Error { get; set; }
}

public class ReadPakAssetsResult
{
    public List<PakBitmap> Bitmaps { get; set; } = [];
    public List<PakRefs> Trees { get; set; } = [];
}

/// <summary>
/// Reads the default game assets of a pak extract for the Blender default asset library:
/// every *.Texture.Gbx (CPlugBitmap settings as BitmapConfig + its image) and the file references of every
/// *.VegetTreeModel.Gbx (only the reference table is read, the body of many tree models can't be parsed).
/// Progress lines "PROGRESS: i/n" go to stdout.
/// </summary>
public class ReadPakAssets : ICommand
{
    public const string COMMAND_NAME = "read-pak-assets";
    static readonly HashSet<string> ImageExtensions = [".dds", ".tga", ".png", ".jpg", ".webp"];

    static readonly JsonSerializerOptions OutputOptions = new()
    {
        WriteIndented = true,
        Converters =
        {
            new JsonStringEnumConverter(),
            new blendermania_dotnet.Vec2ArrayConverter(),
            new blendermania_dotnet.ColorArrayConverter(),
        },
    };

    public static Task<int> Execute(string payload)
    {
        ReadPakAssetsPayload input;
        try
        {
            input = JsonSerializer.Deserialize<ReadPakAssetsPayload>(payload)!;
        }
        catch (Exception ex)
        {
            Console.WriteLine(ex.Message);
            return Task.FromResult((int)ExitCodes.InvalidPayload);
        }
        if (!Directory.Exists(input.Root))
        {
            Console.WriteLine($"Folder not found: {input.Root}");
            return Task.FromResult((int)ExitCodes.InvalidPayload);
        }

        var root = System.IO.Path.GetFullPath(input.Root);
        var bitmaps = Directory.EnumerateFiles(root, "*.Texture.Gbx", SearchOption.AllDirectories).ToList();
        var trees = Directory.EnumerateFiles(root, "*.VegetTreeModel.Gbx", SearchOption.AllDirectories).ToList();
        int total = bitmaps.Count + trees.Count, done = 0;
        var result = new ReadPakAssetsResult();

        foreach (var file in bitmaps)
        {
            var entry = new PakBitmap { Path = Rel(root, file) };
            try
            {
                var gbx = Gbx.Parse<CPlugBitmap>(file);
                entry.Config = ToConfig(gbx.Node);
                // only real image files: some bitmaps reference a Decal / TextureArray instead (can't be rebuilt from an image)
                var image = gbx.RefTable?.Files.FirstOrDefault(f => ImageExtensions.Contains(System.IO.Path.GetExtension(f.FilePath).ToLowerInvariant()));
                if (image is not null)
                    entry.Image = Rel(root, Resolve(file, gbx.RefTable!.AncestorLevel, image.FilePath));
            }
            catch (Exception ex)
            {
                entry.Error = ex.Message;
            }
            result.Bitmaps.Add(entry);
            Progress(++done, total);
        }

        foreach (var file in trees)
        {
            var entry = new PakRefs { Path = Rel(root, file) };
            try
            {
                var gbx = Gbx.Parse(file, new GbxReadSettings { ReadRawBody = true });
                foreach (var r in gbx.RefTable?.Files ?? [])
                    entry.Refs.Add(Rel(root, Resolve(file, gbx.RefTable!.AncestorLevel, r.FilePath)));
            }
            catch (Exception ex)
            {
                entry.Error = ex.Message;
            }
            result.Trees.Add(entry);
            Progress(++done, total);
        }

        File.WriteAllText(input.OutputPath, JsonSerializer.Serialize(result, OutputOptions));
        Console.WriteLine($"SUCCESS: {result.Bitmaps.Count} bitmaps, {result.Trees.Count} tree models -> {input.OutputPath}");
        return Task.FromResult((int)ExitCodes.Success);
    }

    static void Progress(int done, int total)
    {
        if (done % 25 == 0 || done == total)
            Console.WriteLine($"PROGRESS: {done}/{total}");
    }

    /// <summary>ref table path: from the file's folder go up AncestorLevel folders, then the (possibly ..\) path</summary>
    static string Resolve(string file, int ancestorLevel, string refPath)
    {
        var dir = System.IO.Path.GetDirectoryName(file)!;
        for (int i = 0; i < ancestorLevel && dir is not null; i++)
            dir = System.IO.Path.GetDirectoryName(dir)!;
        return System.IO.Path.GetFullPath(System.IO.Path.Combine(dir!, refPath.Replace('\\', System.IO.Path.DirectorySeparatorChar)));
    }

    static string Rel(string root, string path) => System.IO.Path.GetRelativePath(root, path).Replace('\\', '/');

    /// <summary>inverse of CPlugBitmapConverter.CreateBitmapFromConfig</summary>
    static BitmapConfig ToConfig(CPlugBitmap b) => new()
    {
        Usage = b.Usage,
        BumpScaleFactor = b.BumpScaleFactor,
        BumpScaleMipLevel = b.BumpScaleMipLevel,
        BorderRGB = System.Drawing.Color.FromArgb(unchecked((int)0xFF000000) | (b.BorderRGB & 0xFFFFFF)),
        ClearColor = System.Drawing.Color.FromArgb(unchecked((int)b.ClearColor)),
        DefaultRenderClearColor = System.Drawing.Color.FromArgb(unchecked((int)b.DefaultRenderClearColor)),
        DefaultTexCoordRotate = b.DefaultTexCoordRotate,
        DefaultTexCoordScale = b.DefaultTexCoordScale,
        DefaultTexCoordTrans = b.DefaultTexCoordTrans,
        GrassId = b.GrassId ?? "",
        GrassIdTexCoordRotate = b.GrassIdTexCoordRotate,
        GrassIdTexCoordSize = b.GrassIdTexCoordSize,
        GrassIdTexCoordTrans = b.GrassIdTexCoordTrans,
        HeightInMeters = b.HeightInMeters,
        MipMapFadeAlphas = b.MipMapFadeAlphas ?? [],
        MipMapLodBiasDefault = b.MipMapLodBiasDefault,
        MipMapLowerAlpha = b.MipMapLowerAlpha,
        PixelUpdate = b.PixelUpdate,
        RenderSizeDiv = b.RenderSizeDiv,
        RenderSizeMul = b.RenderSizeMul,
    };
}
