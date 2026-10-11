// using System;
// using System.Collections.Generic;
// using System.Linq;
// using System.Text;
// using System.Threading.Tasks;
// using System.Text.Json;

// using GBX.NET;
// using GBX.NET.Engines.Game;

// namespace blendermania_dotnet
// {
//     class InGameMediaTrackerClips
//     {
//         public string? ClipName { get; set; }
//         public List<Int3> Triggers { get; set; } = new();
//     }

//     public class MediaTrackerClipsData
//     {
//         public MediaTrackerClipsData(string MapPath)
//         {
//             this.MapPath = MapPath;
//         }
//         public string MapPath { get; set; }

//         public string WriteJsonFileGetPath()
//         {
//             var map = Gbx.ParseNode<CGameCtnChallenge>(MapPath);
//             var clips = map.ClipGroupInGame?.Clips;
//             var jsonPath = MapPath + ".MediatrackerData.json";

//             List<InGameMediaTrackerClips> igClips = new();

//             if (clips is not null)
//                 foreach (var clip in clips)
//                 {
//                     var igClip = new InGameMediaTrackerClips
//                     {
//                         ClipName = clip.Clip.Name
//                     };

//                     foreach (var coord in clip.Trigger.Coords ?? [])
//                     {
//                         igClip.Triggers.Add(new Int3
//                         {
//                             X = coord.X,
//                             Y = coord.Y,
//                             Z = coord.Z
//                         });
//                     }
//                     igClips.Add(igClip);
//                 }
//             else
//                 igClips.Add(new() { ClipName = "None found" });

//             var data = JsonSerializer.Serialize(igClips);

//             File.WriteAllText(jsonPath, data);

//             return jsonPath;
//         }
//     }
//     class PlaceMediaTrackerClipOnMap
//     {
//         public string? MapPath { get; set; }
//         public List<MediaTrackerClip> Clips { get; set; } = new();

//         async public Task Exec()
//         {
//             if (MapPath is null || MapPath.Length == 0)
//             {
//                 throw new Exception("Map file path is null or empty");
//             }

//             // parse map
//             var map = Gbx.ParseNode<CGameCtnChallenge>(MapPath);

//             var map_clips = map.ClipGroupInGame?.Clips;

//             if (map_clips is null)
//                 return;


//             foreach (var clip in Clips)
//             {
//                 CGameCtnMediaClipGroup.ClipTrigger? map_clip = null;

//                 foreach (var mclip in map_clips)
//                 {
//                     if (mclip.Clip.Name == clip.Name)
//                     {
//                         map_clip = mclip;
//                         break;
//                     }
//                 }

//                 if (map_clip is null)
//                     continue;

//                 var newCoords = new List<Int3>();

//                 foreach (var pos in clip.Positions)
//                 {
//                     newCoords.Add(new Int3
//                     {
//                         X = pos.X,
//                         Y = pos.Y,
//                         Z = pos.Z
//                     });
//                 }

//                 var coordsArray = newCoords.ToArray();

//                 map_clip.Value.Trigger.Coords = coordsArray;
//             }

//             // TODO new map prefix?
//             var NewPath = MapPath;

//             map.Save(NewPath);

//         }


//     }
// }
