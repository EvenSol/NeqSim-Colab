/*
 * To change this license header, choose License Headers in Project Properties. To change this
 * template file, choose Tools | Templates and open the template in the editor.
 */
package com.equinor.neqsimapi;
import com.equinor.neqsimapi.dto.CalcResponse;
import java.sql.Connection;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import javax.ws.rs.Consumes;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import javax.ws.rs.QueryParam;
import javax.ws.rs.GET;

@Path("/ML")
public class NeqSimAPIController {

    private static final Logger LOGGER = LogManager.getLogger(NeqSimAPIController.class.getName());

    private enum CALC_STATUS {
        SUCCESS, ERROR
    }


    private static Connection conn;

    private void validateKey(String key) {
        try {
            if (!System.getenv("ENDPOINT_ACCESS_KEY").equals(key)) {
                throw new SecurityException("Wrong key");
            }
        } catch (Exception ex) {
            throw new SecurityException("Error providing access");
        }
    }

    @GET
    public String index() {
        return "<h1>NeqSim TEG process API</h1>";
    }

    @POST
    @Path("/dehydTEGsim")
    @Produces(MediaType.APPLICATION_JSON)
    @Consumes(MediaType.APPLICATION_JSON)
    public Response dehydAndRegenSimML(com.equinor.neqsimapi.dto.TEGdehydrationRequest req,
            @QueryParam("key") String key) {
        try {
            if (!req.checkValidInput()) {
                return Response.ok(new CalcResponse(new Exception("not valid input to calculation")))
                        .build();
            }
            com.equinor.neqsimapi.model.TEGsim Tegsim1 =
                    new com.equinor.neqsimapi.model.TEGsim();
            neqsim.processSimulation.processSystem.ProcessSystem operations =
                    Tegsim1.getProcess(req);
            Thread processThread = operations.runAsThread();
            try{
                processThread.join(60000 * 5);
            }
            catch(Exception e){
                return Response.ok(new CalcResponse(new Exception("calculation did not finish in maximum time")))
                        .build();
            }  
            return Response.ok(new CalcResponse(operations))
                    .build();
        } catch (Exception ex) {
            return Response.ok(new CalcResponse(ex))
                    .build();
        }
    }

    }
