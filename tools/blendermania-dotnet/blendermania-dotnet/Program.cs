using GBX.NET;
using GBX.NET.LZO;
using GBX.NET.Engines.Game;
using blendermania_dotnet;
using System.Text.Json;
using GBX.NET.Exceptions;
using System.Diagnostics.CodeAnalysis;

// run to debug:
// dotnet run -- <command> <jsonpayloadpath>

// run to publish:
// dotnet publish -r win-x64 -p:PublishSingleFile=true --self-contained true -c Release

// run to start
// blendermania-dotnet.exe <command> <jsonpayloadpath>

// PAYLOAD example for "place-objects-on-map"
/*
{
    "Path": "C:/Users/Vladimir/Documents/Trackmania/Maps/Debuger/TestMap.Map.Gbx",
    "Items": [
        {
            "Name": "TestItem.Item.Gbx",
            "Path": "C:/Users/Vladimir/Documents/Trackmania/Items/TestItem.Item.Gbx",
            "Position": {"X": 0,"Y": 0,"Z": 0},
            "Rotation": {"X": 0,"Y": 0,"Z": 0},
            "Pivot": {"X": 0,"Y": 0,"Z": 0}
        }
    ]
}
*/



Gbx.LZO = new Lzo();

try
{

    var command = args.ElementAtOrDefault(0);
    if (string.IsNullOrEmpty(command))
    {
        Console.WriteLine("Command is not provided");
        return (int)ExitCodes.InvalidPayload;
    }

    var payload = args.ElementAtOrDefault(1);
    if (string.IsNullOrEmpty(payload))
    {
        Console.WriteLine("Payload path is not provided");
        return (int)ExitCodes.InvalidPayload;
    }




    switch (command)
    {
        case PlaceObjectsOnMap.COMMAND_NAME:
            return await PlaceObjectsOnMap.Execute(payload);
        case ConvertFbxToGbx.COMMAND_NAME:
            return await ConvertFbxToGbx.Execute(payload);

        default:
            throw new Exception("No such command: " + command);
    }
}


catch (Exception err)
{
    Console.WriteLine("Error: " + err.Message);
    return (int)ExitCodes.UnknownError;

}