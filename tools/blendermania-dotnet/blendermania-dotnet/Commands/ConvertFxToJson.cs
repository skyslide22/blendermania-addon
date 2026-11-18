using GBX.NET;
using GBX.NET.Engines.MwFoundations;
using System.Text.Json;
using TM_GenericMapping.Items.MeshCompilation;

public class ConvertFxToJsonPayload
{
    /// <summary>*.ParticleModel.Gbx (CPlugParticleEmitterModel) or *.FxSys.Gbx (CPlugFxSystem).</summary>
    public string GbxPath { get; set; } = "";
    /// <summary>Where the "tm-fx/1" json is written.</summary>
    public string OutputPath { get; set; } = "";
}

/// <summary>Writes a particle GBX as "tm-fx/1" json for the Blender FX editor (Import GBX). Warnings go to stdout.</summary>
public class ConvertFxToJson : ICommand
{
    public const string COMMAND_NAME = "convert-fx-to-json";

    public static Task<int> Execute(string payload)
    {
        ConvertFxToJsonPayload input;
        try
        {
            input = JsonSerializer.Deserialize<ConvertFxToJsonPayload>(payload)!;
        }
        catch (Exception ex)
        {
            Console.WriteLine(ex.Message);
            return Task.FromResult((int)ExitCodes.InvalidPayload);
        }
        if (!File.Exists(input.GbxPath))
        {
            Console.WriteLine($"File not found: {input.GbxPath}");
            return Task.FromResult((int)ExitCodes.InvalidPayload);
        }

        CMwNod? node;
        try
        {
            node = Gbx.ParseNode(input.GbxPath);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Cannot read {input.GbxPath}: {ex.Message}");
            return Task.FromResult((int)ExitCodes.GBXError);
        }
        if (node is null)
        {
            Console.WriteLine($"{input.GbxPath} has no node");
            return Task.FromResult((int)ExitCodes.GBXError);
        }

        var writer = new ParticleFxJsonWriter();
        var doc = writer.WriteDocument(node, Path.GetFileName(input.GbxPath));
        File.WriteAllText(input.OutputPath, doc.ToJsonString(new JsonSerializerOptions { WriteIndented = true }));
        foreach (var w in writer.Warnings)
            Console.WriteLine("WARNING: " + w);
        Console.WriteLine($"SUCCESS: {node.GetType().Name} -> {input.OutputPath}");
        return Task.FromResult((int)ExitCodes.Success);
    }
}
